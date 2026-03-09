mod config;
mod connect;
mod flash;
mod mesh;
mod status;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "sp", about = "Solarpunk mesh CLI", version)]
struct Cli {
    /// Hub hostname or IP
    #[arg(long, default_value = config::DEFAULT_HOST, global = true)]
    host: String,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Connect to interactive terminal via WebSocket
    Connect {
        /// Hub host override
        dest: Option<String>,
        /// Web terminal port
        #[arg(short, long, default_value_t = config::DEFAULT_TERMINAL_PORT)]
        port: u16,
    },
    /// Mesh bridge commands
    Mesh {
        #[command(subcommand)]
        action: MeshAction,
    },
    /// Query ESP32 node status directly
    Status {
        /// Node IP address
        #[arg(default_value = "10.42.0.2")]
        node_ip: String,
    },
    /// Build and flash firmware via idf.py
    Flash {
        /// Serial port
        #[arg(short, long, default_value = "/dev/ttyUSB0")]
        port: String,
        /// Target chip
        #[arg(short, long, default_value = "esp32s3")]
        target: String,
    },
}

#[derive(Subcommand)]
pub enum MeshAction {
    /// Show mesh network status
    Status,
    /// Send command to a node through the bridge
    Send {
        /// Node IP address
        node_ip: String,
        /// Command to execute
        cmd: Vec<String>,
    },
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    let result = match cli.command {
        Commands::Connect { dest, port } => {
            let host = dest.unwrap_or(cli.host);
            connect::run(&host, port).await
        }
        Commands::Mesh { action } => mesh::run(&cli.host, action).await,
        Commands::Status { node_ip } => status::run(&node_ip).await,
        Commands::Flash { port, target } => flash::run(&port, &target).await,
    };

    if let Err(e) = result {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}
