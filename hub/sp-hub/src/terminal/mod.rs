mod pty;

use crate::config;
use axum::{
    Router,
    extract::{State, ws},
    response::Html,
    routing::get,
};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;

pub type Sessions = Arc<Mutex<HashMap<u64, pty::PtySession>>>;

pub fn new_sessions() -> Sessions {
    Arc::new(Mutex::new(HashMap::new()))
}

#[derive(Clone)]
struct AppState {
    sessions: Sessions,
}

pub fn router(sessions: Sessions) -> Router {
    let state = AppState { sessions };
    Router::new()
        .route("/", get(index))
        .route("/ws", get(ws_handler))
        .route("/health", get(health))
        .route("/kill", axum::routing::post(kill_all))
        .with_state(state)
}

async fn index() -> Html<&'static str> {
    Html(include_str!("../../static/terminal.html"))
}

async fn health(State(state): State<AppState>) -> axum::Json<serde_json::Value> {
    let sessions = state.sessions.lock().await;
    let mut info = serde_json::json!({
        "sessions": sessions.len(),
        "max_sessions": config::MAX_SESSIONS,
    });
    for (sid, s) in sessions.iter() {
        info[format!("session_{sid}")] = serde_json::json!({
            "pid": s.pid,
            "alive": s.alive,
            "age": s.created.elapsed().as_secs(),
            "idle": s.last_activity.elapsed().as_secs(),
        });
    }
    axum::Json(info)
}

async fn kill_all(State(state): State<AppState>) -> axum::Json<serde_json::Value> {
    let mut sessions = state.sessions.lock().await;
    let count = sessions.len();
    for (_, session) in sessions.drain() {
        pty::kill_session(&session);
    }
    axum::Json(serde_json::json!({"killed": count}))
}

async fn ws_handler(
    State(state): State<AppState>,
    ws: ws::WebSocketUpgrade,
) -> impl axum::response::IntoResponse {
    ws.on_upgrade(move |socket| handle_ws(socket, state))
}

async fn handle_ws(mut socket: ws::WebSocket, state: AppState) {
    // Check session limit
    {
        let sessions = state.sessions.lock().await;
        let active = sessions.values().filter(|s| s.alive).count();
        if active >= config::MAX_SESSIONS {
            let msg = serde_json::json!({"type": "error", "message": format!("max sessions ({}) reached", config::MAX_SESSIONS)});
            let _ = socket.send(ws::Message::Text(msg.to_string().into())).await;
            let _ = socket.send(ws::Message::Close(None)).await;
            return;
        }
    }

    // Fork PTY
    let session = match pty::fork_pty() {
        Ok(s) => s,
        Err(e) => {
            let msg = serde_json::json!({"type": "error", "message": format!("PTY fork failed: {e}")});
            let _ = socket.send(ws::Message::Text(msg.to_string().into())).await;
            return;
        }
    };

    let sid = session.pid as u64;
    let master_fd = session.master_fd;

    {
        let mut sessions = state.sessions.lock().await;
        sessions.insert(sid, session);
    }

    // Set master_fd non-blocking
    unsafe {
        let flags = libc::fcntl(master_fd, libc::F_GETFL);
        libc::fcntl(master_fd, libc::F_SETFL, flags | libc::O_NONBLOCK);
    }

    // Create an AsyncFd for the PTY master
    let async_fd = match tokio::io::unix::AsyncFd::new(master_fd) {
        Ok(fd) => fd,
        Err(e) => {
            tracing::error!("AsyncFd failed: {e}");
            cleanup_session(&state.sessions, sid).await;
            return;
        }
    };

    handle_ws_inner(&mut socket, &async_fd, master_fd, &state.sessions, sid).await;

    // Cleanup - forget AsyncFd so it doesn't close the fd (kill_session handles that)
    std::mem::forget(async_fd);
    cleanup_session(&state.sessions, sid).await;
}

async fn handle_ws_inner(
    socket: &mut ws::WebSocket,
    async_fd: &tokio::io::unix::AsyncFd<i32>,
    master_fd: i32,
    sessions: &Sessions,
    sid: u64,
) {
    let mut buf = vec![0u8; config::READ_BUFFER];

    loop {
        tokio::select! {
            // PTY readable
            readable = async_fd.readable() => {
                match readable {
                    Ok(mut guard) => {
                        let n = unsafe { libc::read(master_fd, buf.as_mut_ptr() as *mut libc::c_void, buf.len()) };
                        if n > 0 {
                            let data = buf[..n as usize].to_vec();
                            if socket.send(ws::Message::Binary(data.into())).await.is_err() {
                                break;
                            }
                            if let Some(s) = sessions.lock().await.get_mut(&sid) {
                                s.touch();
                            }
                        } else if n == 0 {
                            break;
                        } else {
                            let err = std::io::Error::last_os_error();
                            if err.kind() == std::io::ErrorKind::WouldBlock {
                                guard.clear_ready();
                            } else {
                                break;
                            }
                        }
                    }
                    Err(_) => break,
                }
            }
            // WebSocket message
            msg = socket.recv() => {
                match msg {
                    Some(Ok(ws::Message::Text(text))) => {
                        if text.starts_with('{') {
                            if let Ok(val) = serde_json::from_str::<serde_json::Value>(text.as_str()) {
                                if val.get("type").and_then(|t| t.as_str()) == Some("resize") {
                                    if let (Some(rows), Some(cols)) = (
                                        val.get("rows").and_then(|r| r.as_u64()),
                                        val.get("cols").and_then(|c| c.as_u64()),
                                    ) {
                                        pty::set_pty_size(master_fd, rows as u16, cols as u16);
                                    }
                                    continue;
                                }
                                if val.get("type").and_then(|t| t.as_str()) == Some("ping") {
                                    let pong = serde_json::json!({"type": "pong"});
                                    let _ = socket.send(ws::Message::Text(pong.to_string().into())).await;
                                    continue;
                                }
                            }
                        }
                        // Terminal input
                        let bytes = text.as_bytes();
                        let written = unsafe { libc::write(master_fd, bytes.as_ptr() as *const libc::c_void, bytes.len()) };
                        if written < 0 {
                            break;
                        }
                        if let Some(s) = sessions.lock().await.get_mut(&sid) {
                            s.touch();
                        }
                    }
                    Some(Ok(ws::Message::Binary(data))) => {
                        let written = unsafe { libc::write(master_fd, data.as_ptr() as *const libc::c_void, data.len()) };
                        if written < 0 {
                            break;
                        }
                        if let Some(s) = sessions.lock().await.get_mut(&sid) {
                            s.touch();
                        }
                    }
                    Some(Ok(ws::Message::Close(_))) | None => break,
                    _ => {}
                }
            }
        }
    }
}

async fn cleanup_session(sessions: &Sessions, sid: u64) {
    let mut sessions = sessions.lock().await;
    if let Some(session) = sessions.remove(&sid) {
        pty::kill_session(&session);
    }
}

pub async fn reap_zombies(sessions: Sessions) {
    loop {
        tokio::time::sleep(std::time::Duration::from_secs(config::REAPER_INTERVAL_SECS)).await;
        let mut sessions = sessions.lock().await;
        let mut dead = Vec::new();

        for (&sid, session) in sessions.iter() {
            let alive = unsafe { libc::kill(session.pid, 0) == 0 };
            if !alive {
                dead.push(sid);
                continue;
            }
            if session.last_activity.elapsed().as_secs() > config::SESSION_TIMEOUT_SECS {
                pty::kill_session(session);
                dead.push(sid);
            }
        }

        for sid in dead {
            sessions.remove(&sid);
        }

        // Reap zombie children
        loop {
            let ret = unsafe { libc::waitpid(-1, std::ptr::null_mut(), libc::WNOHANG) };
            if ret <= 0 {
                break;
            }
        }
    }
}
