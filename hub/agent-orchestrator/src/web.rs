use crate::orchestrator::Orchestrator;
use crate::types::*;
use axum::{
    extract::State,
    http::StatusCode,
    response::Html,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::info;

type SharedOrch = Arc<Mutex<Orchestrator>>;

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

pub async fn run_web(config: OrchestratorConfig, port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let mut orch = Orchestrator::new(config);
    // Spawn a default agent
    let _ = orch.spawn_agent("assistant", AgentRole::General);

    let state: SharedOrch = Arc::new(Mutex::new(orch));

    let app = Router::new()
        .route("/", get(index_page))
        .route("/api/chat", post(api_chat))
        .route("/api/agents", get(api_list_agents))
        .route("/api/spawn", post(api_spawn))
        .route("/api/health", get(api_health))
        .with_state(state);

    let addr = format!("0.0.0.0:{port}");
    info!("Solarpunk Agent web UI at http://0.0.0.0:{port}");
    println!("\n  Solarpunk Agent running at http://0.0.0.0:{port}");
    println!("  Open this URL on your phone to use it.\n");

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

async fn api_health() -> Json<serde_json::Value> {
    Json(serde_json::json!({ "status": "ok", "version": env!("CARGO_PKG_VERSION") }))
}

async fn api_list_agents(State(orch): State<SharedOrch>) -> Json<Vec<AgentInfo>> {
    let o = orch.lock().await;
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
    State(orch): State<SharedOrch>,
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

    let mut o = orch.lock().await;
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
    State(orch): State<SharedOrch>,
    Json(req): Json<ChatRequest>,
) -> Json<ChatResponse> {
    let mut o = orch.lock().await;

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

async fn index_page() -> Html<&'static str> {
    Html(include_str!("web_ui.html"))
}
