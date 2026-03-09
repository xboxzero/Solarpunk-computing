use crate::config;
use serde::Deserialize;

#[derive(Deserialize)]
struct NodeStatus {
    node: Option<String>,
    battery_pct: Option<u8>,
    battery_mv: Option<u32>,
    solar_mv: Option<u32>,
    charging: Option<bool>,
    peers: Option<u32>,
    uptime_s: Option<u64>,
    llm_connected: Option<bool>,
    firmware: Option<String>,
    encrypted: Option<bool>,
}

pub async fn run(node_ip: &str) -> Result<(), Box<dyn std::error::Error>> {
    let url = format!("http://{}:{}/api/status", node_ip, config::DEFAULT_ESP32_PORT);
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()?;

    let resp = client.get(&url).send().await?;
    let status: NodeStatus = resp.json().await?;

    println!("=== {} ===", status.node.as_deref().unwrap_or("unknown"));
    println!(
        "  battery:  {}% ({}mV){}",
        status.battery_pct.unwrap_or(0),
        status.battery_mv.unwrap_or(0),
        if status.charging.unwrap_or(false) { " [charging]" } else { "" }
    );
    println!("  solar:    {}mV", status.solar_mv.unwrap_or(0));
    println!("  peers:    {}", status.peers.unwrap_or(0));
    println!("  uptime:   {}", format_uptime(status.uptime_s.unwrap_or(0)));
    println!("  firmware: {}", status.firmware.as_deref().unwrap_or("?"));
    println!(
        "  encrypt:  {}",
        if status.encrypted.unwrap_or(false) { "AES-256-GCM" } else { "off" }
    );
    println!(
        "  llm:      {}",
        if status.llm_connected.unwrap_or(false) { "connected" } else { "disconnected" }
    );

    Ok(())
}

fn format_uptime(secs: u64) -> String {
    if secs < 60 {
        format!("{secs}s")
    } else if secs < 3600 {
        format!("{}m {}s", secs / 60, secs % 60)
    } else {
        format!("{}h {}m", secs / 3600, (secs % 3600) / 60)
    }
}
