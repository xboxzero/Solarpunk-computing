use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Clone, Serialize, Deserialize)]
pub struct MeshNode {
    pub name: String,
    pub ip: String,
    pub mac: String,
    pub battery: u8,
    pub solar_mv: u32,
    pub peer_count: u32,
    pub peers: Vec<serde_json::Value>,
    pub uptime: u64,
    pub version: String,
    pub encrypted: bool,
    pub online: bool,
    pub last_seen: u64,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct MeshPeer {
    pub name: String,
    pub battery: Option<u8>,
    pub rssi: Option<i32>,
    pub hops: Option<u32>,
    pub seen_by: Option<String>,
    pub timestamp: u64,
}

#[derive(Default)]
pub struct MeshBridgeState {
    pub nodes: HashMap<String, MeshNode>,
    pub mesh_peers: HashMap<String, MeshPeer>,
}

impl MeshBridgeState {
    pub fn to_json(&self) -> serde_json::Value {
        serde_json::json!({
            "nodes": self.nodes_json(),
            "peers": &self.mesh_peers,
            "bridge_hash": "sp-hub",
        })
    }

    pub fn nodes_json(&self) -> HashMap<String, serde_json::Value> {
        self.nodes
            .iter()
            .map(|(ip, n)| (ip.clone(), serde_json::to_value(n).unwrap_or_default()))
            .collect()
    }
}
