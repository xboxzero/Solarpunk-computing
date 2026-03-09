use crate::types::*;
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::{info, warn};

/// File-based persistence for tasks and agent configs
pub struct Persistence {
    data_dir: PathBuf,
}

impl Persistence {
    pub fn new() -> Self {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        let data_dir = PathBuf::from(home).join(".solarpunk");
        if let Err(e) = std::fs::create_dir_all(&data_dir) {
            warn!("Failed to create data dir {:?}: {e}", data_dir);
        }
        info!("Persistence dir: {}", data_dir.display());
        Self { data_dir }
    }

    /// Save all tasks to disk
    pub fn save_tasks(&self, tasks: &HashMap<TaskId, Task>) {
        let path = self.data_dir.join("tasks.json");
        match serde_json::to_string_pretty(tasks) {
            Ok(data) => {
                if let Err(e) = std::fs::write(&path, &data) {
                    warn!("Failed to save tasks: {e}");
                }
            }
            Err(e) => warn!("Failed to serialize tasks: {e}"),
        }
    }

    /// Load tasks from disk
    pub fn load_tasks(&self) -> HashMap<TaskId, Task> {
        let path = self.data_dir.join("tasks.json");
        match std::fs::read_to_string(&path) {
            Ok(data) => match serde_json::from_str(&data) {
                Ok(tasks) => {
                    let tasks: HashMap<TaskId, Task> = tasks;
                    info!("Loaded {} tasks from disk", tasks.len());
                    tasks
                }
                Err(e) => {
                    warn!("Failed to parse tasks.json: {e}");
                    HashMap::new()
                }
            },
            Err(_) => HashMap::new(),
        }
    }

    /// Save agent registry (name + role for re-creation)
    pub fn save_agent_registry(&self, agents: &[(String, String)]) {
        let path = self.data_dir.join("agents.json");
        let data = serde_json::to_string_pretty(agents).unwrap_or_default();
        std::fs::write(path, data).ok();
    }

    /// Load agent registry
    pub fn load_agent_registry(&self) -> Vec<(String, String)> {
        let path = self.data_dir.join("agents.json");
        match std::fs::read_to_string(&path) {
            Ok(data) => serde_json::from_str(&data).unwrap_or_default(),
            Err(_) => Vec::new(),
        }
    }
}
