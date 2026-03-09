mod agent;
mod llm;
mod mcp;
mod orchestrator;
mod persistence;
mod tools;
mod tui;
mod types;
mod web;

use clap::Parser;
use types::*;

#[derive(Parser)]
#[command(name = "solarpunk-agent")]
#[command(about = "Solarpunk AI Agent Orchestrator")]
#[command(version)]
struct Cli {
    /// LLM backend: "claude", "local", or "openai" (auto-detects Claude OAuth if available)
    #[arg(short, long, default_value = "auto")]
    backend: String,

    /// API key (for Claude or OpenAI-compatible)
    #[arg(short, long, env = "ANTHROPIC_API_KEY")]
    api_key: Option<String>,

    /// Model name
    #[arg(short, long, default_value = "claude-sonnet-4-6-20250514")]
    model: String,

    /// LLM endpoint (for local/openai backends)
    #[arg(short, long, default_value = "http://localhost:8080")]
    endpoint: String,

    /// Max agents
    #[arg(long, default_value = "10")]
    max_agents: usize,

    /// Run web UI instead of TUI (for phone/browser access)
    #[arg(short, long)]
    web: bool,

    /// Web UI port
    #[arg(short, long, default_value = "8888")]
    port: u16,
}

/// Try to read Claude Code OAuth token from ~/.claude/.credentials.json
fn read_claude_oauth_token() -> Option<String> {
    let home = std::env::var("HOME").ok()?;
    let path = format!("{home}/.claude/.credentials.json");
    let data = std::fs::read_to_string(&path).ok()?;
    let json: serde_json::Value = serde_json::from_str(&data).ok()?;
    let token = json
        .get("claudeAiOauth")?
        .get("accessToken")?
        .as_str()?
        .to_string();
    // Check if token hasn't expired
    if let Some(expires) = json.get("claudeAiOauth").and_then(|o| o.get("expiresAt")).and_then(|v| v.as_i64()) {
        let now_ms = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as i64;
        if now_ms > expires {
            eprintln!("  Warning: Claude OAuth token expired. Run `claude` to refresh.");
            return None;
        }
    }
    Some(token)
}

fn resolve_backend(cli: &Cli) -> LlmBackend {
    match cli.backend.as_str() {
        "claude" => LlmBackend::Claude {
            api_key: cli.api_key.clone().unwrap_or_default(),
            model: cli.model.clone(),
        },
        "openai" => LlmBackend::OpenAiCompat {
            endpoint: cli.endpoint.clone(),
            api_key: cli.api_key.clone().unwrap_or_default(),
            model: cli.model.clone(),
        },
        "local" => LlmBackend::LocalLlama {
            endpoint: cli.endpoint.clone(),
            model: cli.model.clone(),
        },
        // "auto" - try Claude OAuth first, then API key, then local
        _ => {
            // 1. Check for explicit API key
            if let Some(ref key) = cli.api_key {
                println!("  Using Claude API key");
                return LlmBackend::Claude {
                    api_key: key.clone(),
                    model: cli.model.clone(),
                };
            }
            // 2. Try Claude Code OAuth token
            if let Some(token) = read_claude_oauth_token() {
                println!("  Auto-detected Claude OAuth token from Claude Code");
                return LlmBackend::ClaudeOAuth {
                    access_token: token,
                    model: cli.model.clone(),
                };
            }
            // 3. Fall back to local
            println!("  No Claude credentials found, using local LLM at {}", cli.endpoint);
            LlmBackend::LocalLlama {
                endpoint: cli.endpoint.clone(),
                model: cli.model.clone(),
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let _ = dotenvy::dotenv();
    let cli = Cli::parse();

    let backend = resolve_backend(&cli);

    let config = OrchestratorConfig {
        default_backend: backend,
        max_agents: cli.max_agents,
        max_concurrent_tasks: 5,
        mcp_servers: Vec::new(),
        workspace_dir: ".".into(),
    };

    if cli.web {
        if let Err(e) = web::run_web(config, cli.port).await {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    } else {
        if let Err(e) = tui::run_tui(config).await {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}
