mod agent;
mod llm;
mod orchestrator;
mod tools;
mod tui;
mod types;

use clap::Parser;
use types::*;

#[derive(Parser)]
#[command(name = "solarpunk-agent")]
#[command(about = "Solarpunk AI Agent Orchestrator")]
#[command(version)]
struct Cli {
    /// LLM backend: "claude", "local", or "openai"
    #[arg(short, long, default_value = "local")]
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
}

#[tokio::main]
async fn main() {
    let _ = dotenvy::dotenv();
    let cli = Cli::parse();

    let backend = match cli.backend.as_str() {
        "claude" => LlmBackend::Claude {
            api_key: cli.api_key.unwrap_or_default(),
            model: cli.model,
        },
        "openai" => LlmBackend::OpenAiCompat {
            endpoint: cli.endpoint,
            api_key: cli.api_key.unwrap_or_default(),
            model: cli.model,
        },
        _ => LlmBackend::LocalLlama {
            endpoint: cli.endpoint,
            model: cli.model,
        },
    };

    let config = OrchestratorConfig {
        default_backend: backend,
        max_agents: cli.max_agents,
        max_concurrent_tasks: 5,
        mcp_servers: Vec::new(),
        workspace_dir: ".".into(),
    };

    if let Err(e) = tui::run_tui(config).await {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}
