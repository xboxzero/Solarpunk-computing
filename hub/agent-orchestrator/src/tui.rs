use crate::orchestrator::Orchestrator;
use crate::types::*;
use chrono::Utc;
use crossterm::{
    event::{self, Event, KeyCode, KeyModifiers},
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
    ExecutableCommand,
};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style, Stylize},
    text::{Line, Span, Text},
    widgets::{Block, Borders, Clear, List, ListItem, ListState, Paragraph, Wrap},
    Frame, Terminal,
};
use std::io::stdout;
use std::sync::Arc;
use tokio::sync::Mutex;

/// Which panel is focused
#[derive(Debug, Clone, Copy, PartialEq)]
enum Focus {
    Agents,
    Chat,
    Input,
}

/// TUI application state
pub struct App {
    pub orch: Arc<Mutex<Orchestrator>>,
    pub focus: Focus,
    pub input: String,
    pub cursor_pos: usize,
    pub chat_history: Vec<ChatLine>,
    pub agent_list_state: ListState,
    pub selected_agent: Option<AgentId>,
    pub agent_ids: Vec<AgentId>,
    pub status_msg: String,
    pub should_quit: bool,
    pub waiting: bool,
    pub scroll_offset: u16,
}

#[derive(Debug, Clone)]
pub struct ChatLine {
    pub role: String,
    pub content: String,
    pub color: Color,
}

impl App {
    pub fn new(orch: Orchestrator) -> Self {
        Self {
            orch: Arc::new(Mutex::new(orch)),
            focus: Focus::Input,
            input: String::new(),
            cursor_pos: 0,
            chat_history: vec![ChatLine {
                role: "system".into(),
                content: "Welcome to Solarpunk Agent. Type a message or use commands:\n  /spawn <name> [role]  - Create agent (roles: coder, researcher, sysadmin, mesh, general)\n  /list                 - List agents\n  /task <description>   - Run a task\n  /clear                - Clear chat\n  Tab                   - Switch focus | Ctrl+C - Quit".into(),
                color: Color::DarkGray,
            }],
            agent_list_state: ListState::default(),
            selected_agent: None,
            agent_ids: Vec::new(),
            status_msg: "Ready".into(),
            should_quit: false,
            waiting: false,
            scroll_offset: 0,
        }
    }

    pub fn push_chat(&mut self, role: &str, content: &str, color: Color) {
        self.chat_history.push(ChatLine {
            role: role.into(),
            content: content.into(),
            color,
        });
        // Auto-scroll to bottom
        self.scroll_offset = 0;
    }

    pub fn refresh_agent_list(&mut self, agents: Vec<(AgentId, String, String, String)>) {
        self.agent_ids = agents.iter().map(|(id, ..)| *id).collect();
        if self.selected_agent.is_none() && !self.agent_ids.is_empty() {
            self.selected_agent = Some(self.agent_ids[0]);
            self.agent_list_state.select(Some(0));
        }
    }
}

pub async fn run_tui(config: OrchestratorConfig) -> Result<(), Box<dyn std::error::Error>> {
    // Setup terminal
    enable_raw_mode()?;
    stdout().execute(EnterAlternateScreen)?;
    let backend = ratatui::backend::CrosstermBackend::new(stdout());
    let mut terminal = Terminal::new(backend)?;

    let orch = Orchestrator::new(config);
    let mut app = App::new(orch);

    // Spawn a default general agent
    {
        let mut o = app.orch.lock().await;
        if let Ok(id) = o.spawn_agent("assistant", AgentRole::General) {
            app.selected_agent = Some(id);
            app.agent_ids.push(id);
            app.agent_list_state.select(Some(0));
            app.status_msg = format!("Agent 'assistant' ready");
        }
    }

    // Main loop
    loop {
        terminal.draw(|f| draw_ui(f, &mut app))?;

        if app.should_quit {
            break;
        }

        // Poll for events with timeout so we can update UI during async ops
        if event::poll(std::time::Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                // Global keys
                if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
                    app.should_quit = true;
                    continue;
                }

                match key.code {
                    KeyCode::Tab => {
                        app.focus = match app.focus {
                            Focus::Input => Focus::Agents,
                            Focus::Agents => Focus::Chat,
                            Focus::Chat => Focus::Input,
                        };
                    }
                    _ => match app.focus {
                        Focus::Input => handle_input_key(&mut app, key.code).await,
                        Focus::Agents => handle_agent_key(&mut app, key.code).await,
                        Focus::Chat => handle_chat_key(&mut app, key.code),
                    },
                }
            }
        }
    }

    // Cleanup
    disable_raw_mode()?;
    stdout().execute(LeaveAlternateScreen)?;
    Ok(())
}

async fn handle_input_key(app: &mut App, key: KeyCode) {
    match key {
        KeyCode::Char(c) => {
            app.input.insert(app.cursor_pos, c);
            app.cursor_pos += 1;
        }
        KeyCode::Backspace => {
            if app.cursor_pos > 0 {
                app.cursor_pos -= 1;
                app.input.remove(app.cursor_pos);
            }
        }
        KeyCode::Left => {
            if app.cursor_pos > 0 {
                app.cursor_pos -= 1;
            }
        }
        KeyCode::Right => {
            if app.cursor_pos < app.input.len() {
                app.cursor_pos += 1;
            }
        }
        KeyCode::Home => app.cursor_pos = 0,
        KeyCode::End => app.cursor_pos = app.input.len(),
        KeyCode::Enter => {
            let input = app.input.clone();
            app.input.clear();
            app.cursor_pos = 0;

            if input.trim().is_empty() {
                return;
            }

            process_input(app, &input).await;
        }
        KeyCode::Up => {
            // Scroll chat up
            app.scroll_offset = app.scroll_offset.saturating_add(1);
        }
        KeyCode::Down => {
            app.scroll_offset = app.scroll_offset.saturating_sub(1);
        }
        _ => {}
    }
}

async fn handle_agent_key(app: &mut App, key: KeyCode) {
    match key {
        KeyCode::Up => {
            let i = app.agent_list_state.selected().unwrap_or(0);
            if i > 0 {
                app.agent_list_state.select(Some(i - 1));
                app.selected_agent = app.agent_ids.get(i - 1).copied();
            }
        }
        KeyCode::Down => {
            let i = app.agent_list_state.selected().unwrap_or(0);
            if i + 1 < app.agent_ids.len() {
                app.agent_list_state.select(Some(i + 1));
                app.selected_agent = app.agent_ids.get(i + 1).copied();
            }
        }
        KeyCode::Enter => {
            if let Some(id) = app.selected_agent {
                app.status_msg = format!("Selected agent {}", &id.to_string()[..8]);
                app.focus = Focus::Input;
            }
        }
        _ => {}
    }
}

fn handle_chat_key(app: &mut App, key: KeyCode) {
    match key {
        KeyCode::Up => app.scroll_offset = app.scroll_offset.saturating_add(3),
        KeyCode::Down => app.scroll_offset = app.scroll_offset.saturating_sub(3),
        KeyCode::Home => app.scroll_offset = u16::MAX,
        KeyCode::End => app.scroll_offset = 0,
        _ => {}
    }
}

async fn process_input(app: &mut App, input: &str) {
    // Handle commands
    if input.starts_with('/') {
        handle_command(app, input).await;
        return;
    }

    // Regular chat message
    let Some(agent_id) = app.selected_agent else {
        app.push_chat("system", "No agent selected. Use /spawn <name> first.", Color::Red);
        return;
    };

    app.push_chat("you", input, Color::Cyan);
    app.status_msg = "Thinking...".into();
    app.waiting = true;

    let orch = app.orch.clone();
    let input_owned = input.to_string();

    match orch.lock().await.send_to_agent(&agent_id, &input_owned).await {
        Ok(response) => {
            app.push_chat("agent", &response, Color::Green);
            app.status_msg = "Ready".into();
        }
        Err(e) => {
            app.push_chat("error", &e, Color::Red);
            app.status_msg = format!("Error: {}", &e[..e.len().min(50)]);
        }
    }
    app.waiting = false;
}

async fn handle_command(app: &mut App, input: &str) {
    let parts: Vec<&str> = input.splitn(3, ' ').collect();
    let cmd = parts[0];

    match cmd {
        "/spawn" => {
            let name = parts.get(1).unwrap_or(&"agent");
            let role_str = parts.get(2).unwrap_or(&"general");
            let role = match *role_str {
                "coder" => AgentRole::Coder,
                "researcher" => AgentRole::Researcher,
                "sysadmin" => AgentRole::SysAdmin,
                "mesh" => AgentRole::MeshOperator,
                _ => AgentRole::General,
            };

            let result = {
                let mut o = app.orch.lock().await;
                o.spawn_agent(name, role.clone())
            };
            match result {
                Ok(id) => {
                    app.agent_ids.push(id);
                    app.selected_agent = Some(id);
                    app.agent_list_state.select(Some(app.agent_ids.len() - 1));
                    app.push_chat("system", &format!("Spawned '{name}' ({role_str}) -> {}", &id.to_string()[..8]), Color::Yellow);
                    app.status_msg = format!("Agent '{name}' ready");
                }
                Err(e) => app.push_chat("error", &e, Color::Red),
            }
        }
        "/list" => {
            let agent_info: Vec<(AgentId, String, String, String)> = {
                let o = app.orch.lock().await;
                o.list_agents()
                    .into_iter()
                    .map(|(id, name, role, status)| {
                        (*id, name.to_string(), format!("{role:?}"), format!("{status:?}"))
                    })
                    .collect()
            };
            if agent_info.is_empty() {
                app.push_chat("system", "No agents running.", Color::Yellow);
            } else {
                let mut msg = String::from("Agents:\n");
                for (id, name, role, status) in &agent_info {
                    let marker = if Some(*id) == app.selected_agent { " ← active" } else { "" };
                    msg.push_str(&format!("  {} | {} | {} | {}{}\n", &id.to_string()[..8], name, role, status, marker));
                }
                app.push_chat("system", &msg, Color::Yellow);
            }
        }
        "/task" => {
            let desc = parts.get(1..).map(|p| p.join(" ")).unwrap_or_default();
            if desc.is_empty() {
                app.push_chat("system", "Usage: /task <description>", Color::Yellow);
                return;
            }

            let agent_id = match app.selected_agent {
                Some(id) => id,
                None => {
                    app.push_chat("system", "No agent selected.", Color::Red);
                    return;
                }
            };

            app.push_chat("system", &format!("Running task: {desc}"), Color::Yellow);
            app.status_msg = "Running task...".into();

            let result = {
                let mut o = app.orch.lock().await;
                let task_id = o.create_task(&desc, &desc, Some(agent_id));
                o.run_task(&task_id).await
            };
            match result {
                Ok(output) => {
                    app.push_chat("agent", &output, Color::Green);
                    app.status_msg = "Task complete".into();
                }
                Err(e) => {
                    app.push_chat("error", &e, Color::Red);
                    app.status_msg = "Task failed".into();
                }
            }
        }
        "/clear" => {
            app.chat_history.clear();
            app.push_chat("system", "Chat cleared.", Color::DarkGray);
        }
        _ => {
            app.push_chat("system", &format!("Unknown command: {cmd}"), Color::Red);
        }
    }
}

fn draw_ui(f: &mut Frame, app: &mut App) {
    let size = f.area();

    // Main layout: sidebar | content
    let main_layout = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Length(28),
            Constraint::Min(40),
        ])
        .split(size);

    // Sidebar: agents list + status
    draw_sidebar(f, app, main_layout[0]);

    // Content: chat + input
    let content_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(5),
            Constraint::Length(3),
            Constraint::Length(1),
        ])
        .split(main_layout[1]);

    draw_chat(f, app, content_layout[0]);
    draw_input(f, app, content_layout[1]);
    draw_status_bar(f, app, content_layout[2]);
}

fn draw_sidebar(f: &mut Frame, app: &mut App, area: Rect) {
    let sidebar_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(5),
            Constraint::Length(7),
        ])
        .split(area);

    // Agent list
    let border_style = if app.focus == Focus::Agents {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::DarkGray)
    };

    let items: Vec<ListItem> = app
        .agent_ids
        .iter()
        .enumerate()
        .map(|(i, id)| {
            let is_selected = Some(*id) == app.selected_agent;
            let marker = if is_selected { "▶ " } else { "  " };
            let short_id = &id.to_string()[..8];
            // We don't have the name here easily, so show id
            let style = if is_selected {
                Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::White)
            };
            ListItem::new(format!("{marker}{short_id}")).style(style)
        })
        .collect();

    let agents_block = Block::default()
        .title(" Agents ")
        .borders(Borders::ALL)
        .border_style(border_style);

    let list = List::new(items).block(agents_block);
    f.render_stateful_widget(list, sidebar_layout[0], &mut app.agent_list_state);

    // Help box
    let help_text = vec![
        Line::from("Tab    Switch panel".dark_gray()),
        Line::from("Enter  Send/Select".dark_gray()),
        Line::from("↑↓     Scroll/Select".dark_gray()),
        Line::from("/spawn Create agent".dark_gray()),
        Line::from("Ctrl+C Quit".dark_gray()),
    ];

    let help = Paragraph::new(help_text).block(
        Block::default()
            .title(" Keys ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::DarkGray)),
    );
    f.render_widget(help, sidebar_layout[1]);
}

fn draw_chat(f: &mut Frame, app: &mut App, area: Rect) {
    let border_style = if app.focus == Focus::Chat {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::DarkGray)
    };

    let mut lines: Vec<Line> = Vec::new();
    for entry in &app.chat_history {
        let label_color = entry.color;
        let label = Span::styled(
            format!("[{}] ", entry.role),
            Style::default().fg(label_color).add_modifier(Modifier::BOLD),
        );

        // Split content into wrapped lines
        for (i, line) in entry.content.lines().enumerate() {
            if i == 0 {
                lines.push(Line::from(vec![
                    label.clone(),
                    Span::styled(line, Style::default().fg(Color::White)),
                ]));
            } else {
                let pad = " ".repeat(entry.role.len() + 3);
                lines.push(Line::from(vec![
                    Span::raw(pad),
                    Span::styled(line, Style::default().fg(Color::White)),
                ]));
            }
        }
        lines.push(Line::from(""));
    }

    let total_lines = lines.len() as u16;
    let visible_height = area.height.saturating_sub(2);
    let max_scroll = total_lines.saturating_sub(visible_height);
    let scroll = app.scroll_offset.min(max_scroll);

    let chat = Paragraph::new(lines)
        .block(
            Block::default()
                .title(" Chat ")
                .borders(Borders::ALL)
                .border_style(border_style),
        )
        .wrap(Wrap { trim: false })
        .scroll((total_lines.saturating_sub(visible_height).saturating_sub(scroll), 0));

    f.render_widget(chat, area);
}

fn draw_input(f: &mut Frame, app: &mut App, area: Rect) {
    let border_style = if app.focus == Focus::Input {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::DarkGray)
    };

    let title = if app.waiting { " Input (waiting...) " } else { " Input " };

    let input = Paragraph::new(app.input.as_str()).block(
        Block::default()
            .title(title)
            .borders(Borders::ALL)
            .border_style(border_style),
    );
    f.render_widget(input, area);

    // Show cursor
    if app.focus == Focus::Input {
        f.set_cursor_position((area.x + app.cursor_pos as u16 + 1, area.y + 1));
    }
}

fn draw_status_bar(f: &mut Frame, app: &mut App, area: Rect) {
    let agent_info = match app.selected_agent {
        Some(id) => format!("agent:{}", &id.to_string()[..8]),
        None => "no agent".into(),
    };

    let status = Line::from(vec![
        Span::styled(" SOLARPUNK ", Style::default().fg(Color::Black).bg(Color::Green).bold()),
        Span::raw(" "),
        Span::styled(&agent_info, Style::default().fg(Color::Cyan)),
        Span::raw(" | "),
        Span::styled(&app.status_msg, Style::default().fg(Color::Yellow)),
        Span::raw(" | "),
        Span::styled(
            format!("{} msgs", app.chat_history.len()),
            Style::default().fg(Color::DarkGray),
        ),
    ]);

    let bar = Paragraph::new(status).style(Style::default().bg(Color::DarkGray));
    f.render_widget(bar, area);
}
