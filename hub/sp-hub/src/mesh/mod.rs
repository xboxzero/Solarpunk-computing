mod poller;
mod state;

pub use state::MeshBridgeState;

use crate::config;
use axum::{
    Router,
    extract::{State, ws},
    response::Html,
    routing::{get, post},
};
use std::sync::Arc;
use tokio::sync::{RwLock, broadcast};

#[derive(Clone)]
struct AppState {
    mesh: Arc<RwLock<MeshBridgeState>>,
    broadcast: broadcast::Sender<String>,
}

pub fn router(
    mesh: Arc<RwLock<MeshBridgeState>>,
    broadcast: broadcast::Sender<String>,
) -> Router {
    let state = AppState { mesh, broadcast };
    Router::new()
        .route("/", get(dashboard))
        .route("/api/state", get(api_state))
        .route("/api/cmd", post(api_cmd))
        .route("/ws", get(ws_handler))
        .with_state(state)
}

async fn dashboard() -> Html<&'static str> {
    Html(include_str!("../../static/dashboard.html"))
}

async fn api_state(State(state): State<AppState>) -> axum::Json<serde_json::Value> {
    let mesh = state.mesh.read().await;
    axum::Json(mesh.to_json())
}

#[derive(serde::Deserialize)]
struct CmdRequest {
    node: String,
    cmd: String,
}

async fn api_cmd(
    State(state): State<AppState>,
    axum::Json(body): axum::Json<CmdRequest>,
) -> axum::Json<serde_json::Value> {
    let mesh = state.mesh.read().await;
    let node = match mesh.nodes.get(&body.node) {
        Some(n) => n.clone(),
        None => {
            return axum::Json(serde_json::json!({"error": "node not found"}));
        }
    };
    drop(mesh);

    match send_command(&node, &body.cmd).await {
        Ok(result) => axum::Json(serde_json::json!({"node": node.name, "result": result})),
        Err(e) => axum::Json(serde_json::json!({"error": e.to_string()})),
    }
}

async fn send_command(
    node: &state::MeshNode,
    cmd: &str,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;
    let url = format!(
        "http://{}:{}/api/run?token={}",
        node.ip,
        config::ESP32_PORT,
        config::AUTH_TOKEN
    );
    let resp = client.post(&url).body(cmd.to_string()).send().await?;
    Ok(resp.text().await?)
}

async fn ws_handler(
    State(state): State<AppState>,
    ws: ws::WebSocketUpgrade,
) -> impl axum::response::IntoResponse {
    ws.on_upgrade(move |socket| handle_ws(socket, state))
}

async fn handle_ws(mut socket: ws::WebSocket, state: AppState) {
    let mut rx = state.broadcast.subscribe();

    loop {
        tokio::select! {
            // Broadcast mesh state updates
            Ok(msg) = rx.recv() => {
                if socket.send(ws::Message::Text(msg.into())).await.is_err() {
                    break;
                }
            }
            // Client messages (commands)
            msg = socket.recv() => {
                match msg {
                    Some(Ok(ws::Message::Text(text))) => {
                        if let Ok(val) = serde_json::from_str::<serde_json::Value>(&text) {
                            if val.get("type").and_then(|t| t.as_str()) == Some("cmd") {
                                let node_ip = val.get("node").and_then(|n| n.as_str()).unwrap_or("");
                                let cmd = val.get("cmd").and_then(|c| c.as_str()).unwrap_or("");

                                let mesh = state.mesh.read().await;
                                if let Some(node) = mesh.nodes.get(node_ip) {
                                    let node = node.clone();
                                    drop(mesh);
                                    match send_command(&node, cmd).await {
                                        Ok(result) => {
                                            let resp = serde_json::json!({
                                                "type": "result",
                                                "node": node.name,
                                                "result": result,
                                            });
                                            let _ = socket.send(ws::Message::Text(resp.to_string().into())).await;
                                        }
                                        Err(e) => {
                                            let resp = serde_json::json!({
                                                "type": "error",
                                                "error": e.to_string(),
                                            });
                                            let _ = socket.send(ws::Message::Text(resp.to_string().into())).await;
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Some(Ok(ws::Message::Close(_))) | None => break,
                    _ => {}
                }
            }
        }
    }
}

pub async fn poll_loop(
    mesh: Arc<RwLock<MeshBridgeState>>,
    broadcast: broadcast::Sender<String>,
) {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .unwrap();

    loop {
        poller::discover_and_poll(&client, &mesh).await;

        // Broadcast state to WebSocket clients
        let state = mesh.read().await;
        let json = serde_json::json!({
            "type": "state",
            "nodes": state.nodes_json(),
            "peers": &state.mesh_peers,
            "timestamp": std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
        });
        let _ = broadcast.send(json.to_string());
        drop(state);

        tokio::time::sleep(std::time::Duration::from_secs(config::POLL_INTERVAL_SECS)).await;
    }
}
