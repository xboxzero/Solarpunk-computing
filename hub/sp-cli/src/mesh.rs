use crate::config;
use crate::MeshAction;
use serde::Deserialize;
use std::collections::HashMap;

#[derive(Deserialize)]
struct MeshState {
    nodes: HashMap<String, NodeInfo>,
    peers: HashMap<String, PeerInfo>,
    bridge_hash: Option<String>,
}

#[derive(Deserialize)]
struct NodeInfo {
    name: String,
    #[allow(dead_code)]
    ip: Option<String>,
    battery: u8,
    solar_mv: u32,
    peer_count: u32,
    uptime: u64,
    version: String,
    encrypted: bool,
    online: bool,
}

#[derive(Deserialize)]
struct PeerInfo {
    battery: Option<u8>,
    rssi: Option<i32>,
    hops: Option<u32>,
    seen_by: Option<String>,
}

#[derive(Deserialize)]
struct CmdResult {
    node: Option<String>,
    result: Option<String>,
    error: Option<String>,
}

pub async fn run(host: &str, action: MeshAction) -> Result<(), Box<dyn std::error::Error>> {
    let base = format!("http://{}:{}", host, config::DEFAULT_BRIDGE_PORT);
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    match action {
        MeshAction::Status => {
            let resp = client.get(format!("{base}/api/state")).send().await?;
            let state: MeshState = resp.json().await?;

            if let Some(hash) = &state.bridge_hash {
                println!("bridge: {hash}");
            }

            println!("\n--- ESP32 Nodes ({}) ---", state.nodes.len());
            for (ip, n) in &state.nodes {
                let status = if n.online { "ONLINE" } else { "OFFLINE" };
                println!(
                    "  {} ({ip}) [{status}]",
                    n.name
                );
                println!(
                    "    bat={}%  solar={}mV  peers={}  up={}  fw={}  enc={}",
                    n.battery,
                    n.solar_mv,
                    n.peer_count,
                    format_uptime(n.uptime),
                    n.version,
                    if n.encrypted { "on" } else { "off" }
                );
            }

            println!("\n--- Mesh Peers ({}) ---", state.peers.len());
            for (name, p) in &state.peers {
                println!(
                    "  {name}: bat={}%  rssi={}  hops={}  via={}",
                    p.battery.map(|b| b.to_string()).unwrap_or("?".into()),
                    p.rssi.map(|r| r.to_string()).unwrap_or("?".into()),
                    p.hops.map(|h| h.to_string()).unwrap_or("?".into()),
                    p.seen_by.as_deref().unwrap_or("?"),
                );
            }
        }
        MeshAction::Send { node_ip, cmd } => {
            let command = cmd.join(" ");
            let body = serde_json::json!({ "node": node_ip, "cmd": command });
            let resp = client
                .post(format!("{base}/api/cmd"))
                .json(&body)
                .send()
                .await?;
            let result: CmdResult = resp.json().await?;

            if let Some(err) = result.error {
                eprintln!("error: {err}");
            } else {
                println!(
                    "{}> {}",
                    result.node.as_deref().unwrap_or("?"),
                    result.result.as_deref().unwrap_or("")
                );
            }
        }
    }

    Ok(())
}

fn format_uptime(secs: u64) -> String {
    if secs < 60 {
        format!("{secs}s")
    } else if secs < 3600 {
        format!("{}m", secs / 60)
    } else {
        format!("{}h{}m", secs / 3600, (secs % 3600) / 60)
    }
}
