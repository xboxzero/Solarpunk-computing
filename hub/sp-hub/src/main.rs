mod config;
mod mesh;
mod terminal;

use clap::Parser;
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Parser)]
#[command(name = "sp-hub", about = "Solarpunk hub services", version)]
struct Cli {
    /// Web terminal port
    #[arg(long, default_value_t = config::TERMINAL_PORT)]
    terminal_port: u16,

    /// Mesh bridge port
    #[arg(long, default_value_t = config::BRIDGE_PORT)]
    bridge_port: u16,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "sp_hub=info".into()),
        )
        .init();

    let cli = Cli::parse();

    let sessions = terminal::new_sessions();
    let mesh_state = Arc::new(RwLock::new(mesh::MeshBridgeState::default()));
    let broadcast = tokio::sync::broadcast::Sender::new(32);

    // Build terminal app
    let terminal_app = terminal::router(sessions.clone());
    let terminal_addr: std::net::SocketAddr = ([0, 0, 0, 0], cli.terminal_port).into();

    // Build mesh app
    let mesh_app = mesh::router(mesh_state.clone(), broadcast.clone());
    let mesh_addr: std::net::SocketAddr = ([0, 0, 0, 0], cli.bridge_port).into();

    tracing::info!("Web terminal on http://0.0.0.0:{}", cli.terminal_port);
    tracing::info!("Mesh bridge on http://0.0.0.0:{}", cli.bridge_port);

    // Spawn services
    let terminal_server = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(terminal_addr).await.unwrap();
        axum::serve(listener, terminal_app).await.unwrap();
    });

    let mesh_server = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(mesh_addr).await.unwrap();
        axum::serve(listener, mesh_app).await.unwrap();
    });

    // Spawn zombie reaper
    let reaper_sessions = sessions.clone();
    let reaper = tokio::spawn(async move {
        terminal::reap_zombies(reaper_sessions).await;
    });

    // Spawn mesh poller
    let poller = tokio::spawn(async move {
        mesh::poll_loop(mesh_state, broadcast).await;
    });

    tokio::select! {
        _ = terminal_server => {}
        _ = mesh_server => {}
        _ = reaper => {}
        _ = poller => {}
        _ = tokio::signal::ctrl_c() => {
            tracing::info!("Shutting down...");
        }
    }
}
