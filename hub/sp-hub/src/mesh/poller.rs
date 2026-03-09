use crate::config;
use super::state::{MeshBridgeState, MeshNode, MeshPeer};
use std::sync::Arc;
use tokio::sync::RwLock;

pub async fn discover_and_poll(client: &reqwest::Client, mesh: &Arc<RwLock<MeshBridgeState>>) {
    // Probe subnet concurrently
    let mut tasks = Vec::new();
    for i in config::ESP32_SCAN_START..=config::ESP32_SCAN_END {
        let ip = format!("{}.{i}", config::ESP32_SUBNET);
        let client = client.clone();
        tasks.push(tokio::spawn(async move { probe_node(&client, &ip).await }));
    }

    let mut results = Vec::new();
    for task in tasks {
        if let Ok(result) = task.await {
            results.push(result);
        }
    }

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    {
        let mut state = mesh.write().await;
        for result in results {
            if let Some((ip, node)) = result {
                tracing::debug!("Found node: {} at {ip}", node.name);
                state.nodes.insert(ip, node);
            }
        }

        // Mark offline nodes
        for node in state.nodes.values_mut() {
            if now.saturating_sub(node.last_seen) > config::NODE_EXPIRE_SECS {
                node.online = false;
            }
        }
    }

    // Collect online nodes for peer polling
    let online_nodes: Vec<(String, String)> = {
        let state = mesh.read().await;
        state
            .nodes
            .iter()
            .filter(|(_, n)| n.online)
            .map(|(ip, n)| (ip.clone(), n.name.clone()))
            .collect()
    };

    // Poll mesh peers from each online node
    for (ip, node_name) in &online_nodes {
        if let Some(peers) = poll_peers(client, ip).await {
            let mut state = mesh.write().await;
            for peer in peers {
                if let Some(name) = peer.get("name").and_then(|n| n.as_str()) {
                    if !name.is_empty() {
                        state.mesh_peers.insert(
                            name.to_string(),
                            MeshPeer {
                                name: name.to_string(),
                                battery: peer.get("battery").and_then(|b| b.as_u64()).map(|b| b as u8),
                                rssi: peer.get("rssi").and_then(|r| r.as_i64()).map(|r| r as i32),
                                hops: peer.get("hops").and_then(|h| h.as_u64()).map(|h| h as u32),
                                seen_by: Some(node_name.clone()),
                                timestamp: now,
                            },
                        );
                    }
                }
            }
        }
    }
}

async fn probe_node(client: &reqwest::Client, ip: &str) -> Option<(String, MeshNode)> {
    let url = format!("http://{ip}:{}/api/status", config::ESP32_PORT);
    let resp = client.get(&url).send().await.ok()?;
    if resp.status() != 200 {
        return None;
    }
    let data: serde_json::Value = resp.json().await.ok()?;

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    let node = MeshNode {
        name: data.get("node").and_then(|n| n.as_str()).unwrap_or("unknown").to_string(),
        ip: ip.to_string(),
        mac: data.get("mac").and_then(|m| m.as_str()).unwrap_or("").to_string(),
        battery: data
            .get("battery_pct")
            .or(data.get("battery"))
            .and_then(|b| b.as_u64())
            .unwrap_or(0) as u8,
        solar_mv: data.get("solar_mv").and_then(|s| s.as_u64()).unwrap_or(0) as u32,
        peer_count: data.get("peers").and_then(|p| p.as_u64()).unwrap_or(0) as u32,
        peers: vec![],
        uptime: data
            .get("uptime_s")
            .or(data.get("uptime"))
            .and_then(|u| u.as_u64())
            .unwrap_or(0),
        version: data
            .get("firmware")
            .or(data.get("version"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        encrypted: data.get("encrypted").and_then(|e| e.as_bool()).unwrap_or(false),
        online: true,
        last_seen: now,
    };

    Some((ip.to_string(), node))
}

async fn poll_peers(client: &reqwest::Client, ip: &str) -> Option<Vec<serde_json::Value>> {
    let url = format!("http://{ip}:{}/api/mesh/peers", config::ESP32_PORT);
    let resp = client.get(&url).send().await.ok()?;
    if resp.status() != 200 {
        return None;
    }
    resp.json().await.ok()
}
