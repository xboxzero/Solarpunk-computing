mod config;
mod mesh;
mod recorder;
mod solarmix;
mod terminal;
mod tls;

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

    /// Meeting recorder port (HTTP)
    #[arg(long, default_value_t = config::RECORDER_PORT)]
    recorder_port: u16,

    /// Meeting recorder port (HTTPS, self-signed). Set to 0 to disable.
    /// Required for iPhone Safari mic access (browsers gate getUserMedia behind a secure context).
    #[arg(long, default_value_t = config::RECORDER_TLS_PORT)]
    recorder_tls_port: u16,

    /// Solarmix page port (Leap-controlled feedback rhythm + pi-cam visual).
    #[arg(long, default_value_t = config::SOLARMIX_PORT)]
    solarmix_port: u16,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "sp_hub=info".into()),
        )
        .init();

    // Required because rustls pulls in both aws-lc-rs and ring transitively (via rcgen + reqwest);
    // without this, axum-server panics on first TLS handshake.
    let _ = rustls::crypto::aws_lc_rs::default_provider().install_default();

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

    // Build recorder app
    let recorder_app = recorder::router();
    let recorder_addr: std::net::SocketAddr = ([0, 0, 0, 0], cli.recorder_port).into();

    // Build solarmix app
    let solarmix_app = solarmix::router();
    let solarmix_addr: std::net::SocketAddr = ([0, 0, 0, 0], cli.solarmix_port).into();

    tracing::info!("Web terminal on http://0.0.0.0:{}", cli.terminal_port);
    tracing::info!("Mesh bridge on http://0.0.0.0:{}", cli.bridge_port);
    tracing::info!("Meeting recorder on http://0.0.0.0:{}", cli.recorder_port);
    tracing::info!("Solarmix on http://0.0.0.0:{}", cli.solarmix_port);

    // Optionally provision TLS for the recorder so iPhone Safari can use the mic.
    // getUserMedia requires a secure context; over LAN HTTP, navigator.mediaDevices is undefined.
    let recorder_tls = if cli.recorder_tls_port != 0 {
        let dir = tls::tls_dir();
        match tls::ensure_self_signed(&dir) {
            Ok(t) => {
                tracing::info!(
                    "Meeting recorder on https://0.0.0.0:{} (self-signed; SANs: {})",
                    cli.recorder_tls_port,
                    t.sans.join(", ")
                );
                tracing::info!("TLS material at {}", t.dir.display());
                Some(t)
            }
            Err(e) => {
                tracing::warn!("Could not provision recorder TLS: {e}. iPhone Safari will not be able to use the mic.");
                None
            }
        }
    } else {
        None
    };

    // Spawn services
    let terminal_server = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(terminal_addr).await.unwrap();
        axum::serve(listener, terminal_app).await.unwrap();
    });

    let mesh_server = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(mesh_addr).await.unwrap();
        axum::serve(listener, mesh_app).await.unwrap();
    });

    let recorder_app_for_https = recorder_app.clone();
    let recorder_server = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(recorder_addr).await.unwrap();
        axum::serve(listener, recorder_app).await.unwrap();
    });

    let solarmix_server = tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(solarmix_addr).await.unwrap();
        axum::serve(listener, solarmix_app).await.unwrap();
    });

    let recorder_tls_server = if let Some(t) = recorder_tls {
        let tls_addr: std::net::SocketAddr = ([0, 0, 0, 0], cli.recorder_tls_port).into();
        Some(tokio::spawn(async move {
            let config = match axum_server::tls_rustls::RustlsConfig::from_pem(t.cert_pem, t.key_pem).await {
                Ok(c) => c,
                Err(e) => {
                    tracing::error!("Failed to load recorder TLS config: {e}");
                    return;
                }
            };
            if let Err(e) = axum_server::bind_rustls(tls_addr, config)
                .serve(recorder_app_for_https.into_make_service())
                .await
            {
                tracing::error!("Recorder HTTPS server crashed: {e}");
            }
        }))
    } else {
        None
    };

    // Spawn zombie reaper
    let reaper_sessions = sessions.clone();
    let reaper = tokio::spawn(async move {
        terminal::reap_zombies(reaper_sessions).await;
    });

    // Spawn mesh poller
    let poller = tokio::spawn(async move {
        mesh::poll_loop(mesh_state, broadcast).await;
    });

    let recorder_tls_fut = async {
        match recorder_tls_server {
            Some(h) => { let _ = h.await; }
            None => std::future::pending::<()>().await,
        }
    };

    tokio::select! {
        _ = terminal_server => {}
        _ = mesh_server => {}
        _ = recorder_server => {}
        _ = recorder_tls_fut => {}
        _ = solarmix_server => {}
        _ = reaper => {}
        _ = poller => {}
        _ = tokio::signal::ctrl_c() => {
            tracing::info!("Shutting down...");
        }
    }
}
