use crate::orchestrator::Orchestrator;
use crate::types::*;
use axum::{
    extract::ws::{Message as WsMessage, WebSocket, WebSocketUpgrade},
    extract::State,
    http::StatusCode,
    response::{Html, IntoResponse},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::{broadcast, Mutex};
use tracing::{info, warn};

#[derive(Clone)]
struct WebState {
    orch: Arc<Mutex<Orchestrator>>,
    events: broadcast::Sender<WsEvent>,
}

#[derive(Deserialize)]
pub struct ChatRequest {
    message: String,
    agent_id: Option<String>,
}

#[derive(Serialize)]
pub struct ChatResponse {
    response: String,
    agent_id: String,
    success: bool,
}

#[derive(Deserialize)]
pub struct SpawnRequest {
    name: String,
    role: Option<String>,
}

#[derive(Serialize)]
pub struct SpawnResponse {
    agent_id: String,
    name: String,
    role: String,
    success: bool,
}

#[derive(Serialize)]
pub struct AgentInfo {
    id: String,
    name: String,
    role: String,
    status: String,
}

#[derive(Serialize)]
pub struct TaskInfo {
    id: String,
    title: String,
    description: String,
    status: String,
    assigned_to: Option<String>,
    created_at: String,
    completed_at: Option<String>,
}

pub async fn run_web(
    config: OrchestratorConfig,
    port: u16,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut orch = Orchestrator::new(config);
    // Spawn a default agent
    let _ = orch.spawn_agent("assistant", AgentRole::General);

    let events = orch.event_sender();
    let state = WebState {
        orch: Arc::new(Mutex::new(orch)),
        events,
    };

    let app = Router::new()
        .route("/", get(index_page))
        .route("/api/chat", post(api_chat))
        .route("/api/agents", get(api_list_agents))
        .route("/api/spawn", post(api_spawn))
        .route("/api/health", get(api_health))
        .route("/api/tasks", get(api_list_tasks))
        .route("/api/tasks/create", post(api_create_task))
        .route("/api/tasks/run", post(api_run_task))
        .route("/api/mcp/connect", post(api_mcp_connect))
        .route("/api/mcp/servers", get(api_mcp_servers))
        .route("/api/mcp/tools", get(api_mcp_tools))
        .route("/ws", get(ws_handler))
        .with_state(state);

    let addr = format!("0.0.0.0:{port}");
    info!("Solarpunk Agent web UI at http://0.0.0.0:{port}");
    println!("\n  Solarpunk Agent running at http://0.0.0.0:{port}");
    println!("  Open this URL on your phone to use it.");
    println!("  WebSocket live updates at ws://0.0.0.0:{port}/ws\n");

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

// --- WebSocket handler ---

async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<WebState>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_ws(socket, state.events))
}

async fn handle_ws(mut socket: WebSocket, events: broadcast::Sender<WsEvent>) {
    let mut rx = events.subscribe();
    info!("WebSocket client connected");

    // Send a welcome event
    let welcome = serde_json::json!({
        "type": "Connected",
        "version": env!("CARGO_PKG_VERSION")
    });
    let _ = socket
        .send(WsMessage::Text(welcome.to_string().into()))
        .await;

    loop {
        tokio::select! {
            // Broadcast events -> client
            result = rx.recv() => {
                match result {
                    Ok(event) => {
                        if let Ok(json) = serde_json::to_string(&event) {
                            if socket.send(WsMessage::Text(json.into())).await.is_err() {
                                break; // Client disconnected
                            }
                        }
                    }
                    Err(broadcast::error::RecvError::Lagged(n)) => {
                        // Missed some events, that's ok
                        tracing::warn!("WebSocket lagged by {n} events");
                    }
                    Err(_) => break,
                }
            }
            // Client -> server (handle pings, close)
            msg = socket.recv() => {
                match msg {
                    Some(Ok(WsMessage::Ping(data))) => {
                        let _ = socket.send(WsMessage::Pong(data)).await;
                    }
                    Some(Ok(WsMessage::Close(_))) | None => break,
                    _ => {} // Ignore text/binary from client for now
                }
            }
        }
    }

    info!("WebSocket client disconnected");
}

// --- REST API handlers ---

async fn api_health() -> Json<serde_json::Value> {
    Json(serde_json::json!({ "status": "ok", "version": env!("CARGO_PKG_VERSION") }))
}

async fn api_list_agents(State(state): State<WebState>) -> Json<Vec<AgentInfo>> {
    let o = state.orch.lock().await;
    let agents = o
        .list_agents()
        .into_iter()
        .map(|(id, name, role, status)| AgentInfo {
            id: id.to_string(),
            name: name.to_string(),
            role: format!("{role:?}"),
            status: format!("{status:?}"),
        })
        .collect();
    Json(agents)
}

async fn api_spawn(
    State(state): State<WebState>,
    Json(req): Json<SpawnRequest>,
) -> Result<Json<SpawnResponse>, StatusCode> {
    let role_str = req.role.as_deref().unwrap_or("general");
    let role = match role_str {
        "coder" => AgentRole::Coder,
        "researcher" => AgentRole::Researcher,
        "sysadmin" => AgentRole::SysAdmin,
        "mesh" => AgentRole::MeshOperator,
        _ => AgentRole::General,
    };

    let mut o = state.orch.lock().await;
    match o.spawn_agent(&req.name, role) {
        Ok(id) => Ok(Json(SpawnResponse {
            agent_id: id.to_string(),
            name: req.name,
            role: role_str.to_string(),
            success: true,
        })),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

async fn api_chat(
    State(state): State<WebState>,
    Json(req): Json<ChatRequest>,
) -> Json<ChatResponse> {
    let mut o = state.orch.lock().await;

    // Find agent - use provided ID or first available
    let agent_id = if let Some(id_str) = &req.agent_id {
        uuid::Uuid::parse_str(id_str).ok()
    } else {
        o.list_agents().first().map(|(id, ..)| **id)
    };

    let Some(agent_id) = agent_id else {
        return Json(ChatResponse {
            response: "No agents available. Spawn one first.".into(),
            agent_id: String::new(),
            success: false,
        });
    };

    // Broadcast user message
    let _ = state.events.send(WsEvent::ChatMessage {
        agent_id: agent_id.to_string(),
        role: "user".into(),
        content: req.message.clone(),
    });

    match o.send_to_agent(&agent_id, &req.message).await {
        Ok(response) => Json(ChatResponse {
            response,
            agent_id: agent_id.to_string(),
            success: true,
        }),
        Err(e) => Json(ChatResponse {
            response: format!("Error: {e}"),
            agent_id: agent_id.to_string(),
            success: false,
        }),
    }
}

async fn api_list_tasks(State(state): State<WebState>) -> Json<Vec<TaskInfo>> {
    let o = state.orch.lock().await;
    let tasks = o
        .list_tasks()
        .into_iter()
        .map(|t| TaskInfo {
            id: t.id.to_string(),
            title: t.title.clone(),
            description: t.description.clone(),
            status: format!("{:?}", t.status),
            assigned_to: t.assigned_to.map(|id| id.to_string()),
            created_at: t.created_at.to_rfc3339(),
            completed_at: t.completed_at.map(|dt| dt.to_rfc3339()),
        })
        .collect();
    Json(tasks)
}

#[derive(Deserialize)]
pub struct CreateTaskRequest {
    title: String,
    description: String,
    agent_id: Option<String>,
}

#[derive(Serialize)]
pub struct CreateTaskResponse {
    task_id: String,
    success: bool,
}

async fn api_create_task(
    State(state): State<WebState>,
    Json(req): Json<CreateTaskRequest>,
) -> Json<CreateTaskResponse> {
    let mut o = state.orch.lock().await;
    let assign_to = req
        .agent_id
        .as_deref()
        .and_then(|s| uuid::Uuid::parse_str(s).ok());
    let task_id = o.create_task(&req.title, &req.description, assign_to);

    Json(CreateTaskResponse {
        task_id: task_id.to_string(),
        success: true,
    })
}

// --- MCP endpoints ---

#[derive(Deserialize)]
pub struct McpConnectRequest {
    name: String,
    command: String,
    #[serde(default)]
    args: Vec<String>,
}

#[derive(Serialize)]
pub struct McpConnectResponse {
    name: String,
    tool_count: usize,
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

async fn api_mcp_connect(
    State(state): State<WebState>,
    Json(req): Json<McpConnectRequest>,
) -> Json<McpConnectResponse> {
    let o = state.orch.lock().await;
    match o.connect_mcp_stdio(&req.name, &req.command, &req.args).await {
        Ok(count) => Json(McpConnectResponse {
            name: req.name,
            tool_count: count,
            success: true,
            error: None,
        }),
        Err(e) => {
            warn!("MCP connect failed: {e}");
            Json(McpConnectResponse {
                name: req.name,
                tool_count: 0,
                success: false,
                error: Some(e),
            })
        }
    }
}

#[derive(Serialize)]
pub struct McpServerInfo {
    name: String,
    tool_count: usize,
}

async fn api_mcp_servers(State(state): State<WebState>) -> Json<Vec<McpServerInfo>> {
    let o = state.orch.lock().await;
    let mgr = o.mcp_manager();
    let mgr = mgr.lock().await;
    let servers = mgr
        .list_servers()
        .into_iter()
        .map(|(name, tool_count)| McpServerInfo {
            name: name.to_string(),
            tool_count,
        })
        .collect();
    Json(servers)
}

#[derive(Serialize)]
pub struct McpToolInfo {
    name: String,
    description: String,
    server: String,
}

async fn api_mcp_tools(State(state): State<WebState>) -> Json<Vec<McpToolInfo>> {
    let o = state.orch.lock().await;
    let mgr = o.mcp_manager();
    let mgr = mgr.lock().await;
    let tools = mgr
        .all_tools()
        .into_iter()
        .map(|t| McpToolInfo {
            name: t.name,
            description: t.description,
            server: t.server_name,
        })
        .collect();
    Json(tools)
}

// --- Task run endpoint ---

#[derive(Deserialize)]
pub struct RunTaskRequest {
    task_id: String,
}

#[derive(Serialize)]
pub struct RunTaskResponse {
    success: bool,
    result: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

async fn api_run_task(
    State(state): State<WebState>,
    Json(req): Json<RunTaskRequest>,
) -> Json<RunTaskResponse> {
    let task_id = match uuid::Uuid::parse_str(&req.task_id) {
        Ok(id) => id,
        Err(_) => {
            return Json(RunTaskResponse {
                success: false,
                result: None,
                error: Some("Invalid task ID".into()),
            })
        }
    };

    let mut o = state.orch.lock().await;
    match o.run_task(&task_id).await {
        Ok(output) => Json(RunTaskResponse {
            success: true,
            result: Some(output),
            error: None,
        }),
        Err(e) => Json(RunTaskResponse {
            success: false,
            result: None,
            error: Some(e),
        }),
    }
}

async fn index_page() -> Html<&'static str> {
    Html(include_str!("web_ui.html"))
}
