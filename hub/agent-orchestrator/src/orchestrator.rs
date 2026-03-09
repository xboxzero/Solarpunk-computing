use crate::agent::Agent;
use crate::mcp::McpManager;
use crate::persistence::Persistence;
use crate::types::*;
use chrono::Utc;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{broadcast, Mutex};
use tracing::info;
use uuid::Uuid;

/// The main orchestrator that manages multiple agents
pub struct Orchestrator {
    agents: HashMap<AgentId, Agent>,
    tasks: HashMap<TaskId, Task>,
    config: OrchestratorConfig,
    persistence: Persistence,
    events: broadcast::Sender<WsEvent>,
    mcp_mgr: Arc<Mutex<McpManager>>,
}

impl Orchestrator {
    pub fn new(config: OrchestratorConfig) -> Self {
        info!(
            "Orchestrator starting with max {} agents",
            config.max_agents
        );

        let persistence = Persistence::new();
        let tasks = persistence.load_tasks();
        let (events, _) = broadcast::channel(256);

        if !tasks.is_empty() {
            info!("Restored {} tasks from disk", tasks.len());
        }

        Self {
            agents: HashMap::new(),
            tasks,
            config,
            persistence,
            events,
            mcp_mgr: Arc::new(Mutex::new(McpManager::new())),
        }
    }

    /// Get the event broadcast sender (for WebSocket subscribers)
    pub fn event_sender(&self) -> broadcast::Sender<WsEvent> {
        self.events.clone()
    }

    /// Get a reference to the MCP manager
    pub fn mcp_manager(&self) -> Arc<Mutex<McpManager>> {
        self.mcp_mgr.clone()
    }

    /// Connect an MCP stdio server
    pub async fn connect_mcp_stdio(
        &self,
        name: &str,
        command: &str,
        args: &[String],
    ) -> Result<usize, String> {
        let mut mgr = self.mcp_mgr.lock().await;
        let tools = mgr.connect_stdio(name, command, args).await?;
        let count = tools.len();

        let _ = self.events.send(WsEvent::McpServerConnected {
            name: name.to_string(),
            tool_count: count,
        });

        Ok(count)
    }

    /// Spawn a new agent with a given role
    pub fn spawn_agent(&mut self, name: &str, role: AgentRole) -> Result<AgentId, String> {
        if self.agents.len() >= self.config.max_agents {
            return Err(format!(
                "Max agents reached ({}). Remove an agent first.",
                self.config.max_agents
            ));
        }

        let agent = Agent::new(
            name,
            role.clone(),
            self.config.default_backend.clone(),
            Some(self.mcp_mgr.clone()),
        );
        let id = agent.id;
        info!("Spawned agent '{}' ({:?}) with id {}", name, role, id);

        let _ = self.events.send(WsEvent::AgentSpawned {
            agent_id: id.to_string(),
            name: name.to_string(),
            role: format!("{role:?}"),
        });

        self.agents.insert(id, agent);
        Ok(id)
    }

    /// Send a message to a specific agent
    pub async fn send_to_agent(
        &mut self,
        agent_id: &AgentId,
        message: &str,
    ) -> Result<String, String> {
        let agent = self
            .agents
            .get_mut(agent_id)
            .ok_or_else(|| format!("Agent {agent_id} not found"))?;

        let result = agent.process(message).await;

        // Broadcast the response
        if let Ok(ref response) = result {
            let _ = self.events.send(WsEvent::ChatMessage {
                agent_id: agent_id.to_string(),
                role: "assistant".into(),
                content: response.clone(),
            });
        }

        result
    }

    /// Create a task and optionally assign it
    pub fn create_task(
        &mut self,
        title: &str,
        description: &str,
        assign_to: Option<AgentId>,
    ) -> TaskId {
        let id = Uuid::new_v4();
        let task = Task {
            id,
            title: title.to_string(),
            description: description.to_string(),
            assigned_to: assign_to,
            status: TaskStatus::Pending,
            result: None,
            created_at: Utc::now(),
            completed_at: None,
            parent_task: None,
            subtasks: Vec::new(),
        };
        info!("Created task '{}' ({})", title, id);

        let _ = self.events.send(WsEvent::TaskCreated {
            task_id: id.to_string(),
            title: title.to_string(),
        });

        self.tasks.insert(id, task);
        self.persistence.save_tasks(&self.tasks);
        id
    }

    /// Execute a task with its assigned agent
    pub async fn run_task(&mut self, task_id: &TaskId) -> Result<String, String> {
        let task = self
            .tasks
            .get(task_id)
            .ok_or_else(|| format!("Task {task_id} not found"))?
            .clone();

        let agent_id = task
            .assigned_to
            .ok_or_else(|| "Task has no assigned agent".to_string())?;

        let prompt = format!(
            "Task: {}\n\nDescription: {}\n\nPlease complete this task.",
            task.title, task.description
        );

        // Update task status
        if let Some(t) = self.tasks.get_mut(task_id) {
            t.status = TaskStatus::InProgress;
        }

        let _ = self.events.send(WsEvent::TaskUpdated {
            task_id: task_id.to_string(),
            title: task.title.clone(),
            status: "InProgress".into(),
        });

        self.persistence.save_tasks(&self.tasks);

        let result = self.send_to_agent(&agent_id, &prompt).await;

        // Update task with result
        if let Some(t) = self.tasks.get_mut(task_id) {
            match &result {
                Ok(output) => {
                    t.status = TaskStatus::Completed;
                    t.result = Some(output.clone());
                    t.completed_at = Some(Utc::now());
                }
                Err(err) => {
                    t.status = TaskStatus::Failed(err.clone());
                }
            }
        }

        let status_str = match &result {
            Ok(_) => "Completed",
            Err(_) => "Failed",
        };

        let _ = self.events.send(WsEvent::TaskUpdated {
            task_id: task_id.to_string(),
            title: task.title.clone(),
            status: status_str.into(),
        });

        self.persistence.save_tasks(&self.tasks);
        result
    }

    /// List all agents
    pub fn list_agents(&self) -> Vec<(&AgentId, &str, &AgentRole, &AgentStatus)> {
        self.agents
            .iter()
            .map(|(id, a)| (id, a.name.as_str(), &a.role, &a.status))
            .collect()
    }

    /// List all tasks
    pub fn list_tasks(&self) -> Vec<&Task> {
        self.tasks.values().collect()
    }

    /// Remove an agent
    pub fn remove_agent(&mut self, id: &AgentId) -> Result<(), String> {
        self.agents
            .remove(id)
            .map(|a| {
                info!("Removed agent '{}' ({})", a.name, id);
                let _ = self.events.send(WsEvent::AgentRemoved {
                    agent_id: id.to_string(),
                });
            })
            .ok_or_else(|| format!("Agent {id} not found"))
    }

    /// Auto-assign a task to the best available agent based on role
    pub fn auto_assign(&mut self, task_id: &TaskId) -> Result<AgentId, String> {
        let idle_agent = self
            .agents
            .iter()
            .find(|(_, a)| a.status == AgentStatus::Idle)
            .map(|(id, _)| *id);

        match idle_agent {
            Some(agent_id) => {
                if let Some(task) = self.tasks.get_mut(task_id) {
                    task.assigned_to = Some(agent_id);
                    info!("Auto-assigned task to agent {}", agent_id);
                }
                self.persistence.save_tasks(&self.tasks);
                Ok(agent_id)
            }
            None => Err("No idle agents available".into()),
        }
    }

    /// Cancel a pending task
    pub fn cancel_task(&mut self, task_id: &TaskId) -> Result<(), String> {
        let task = self
            .tasks
            .get_mut(task_id)
            .ok_or_else(|| format!("Task {task_id} not found"))?;

        if task.status == TaskStatus::Pending || task.status == TaskStatus::InProgress {
            task.status = TaskStatus::Cancelled;

            let _ = self.events.send(WsEvent::TaskUpdated {
                task_id: task_id.to_string(),
                title: task.title.clone(),
                status: "Cancelled".into(),
            });

            self.persistence.save_tasks(&self.tasks);
            Ok(())
        } else {
            Err(format!("Task is already {:?}", task.status))
        }
    }

    /// Clean completed/failed/cancelled tasks older than given hours
    pub fn clean_old_tasks(&mut self, max_age_hours: i64) -> usize {
        let cutoff = Utc::now() - chrono::Duration::hours(max_age_hours);
        let before = self.tasks.len();

        self.tasks.retain(|_, task| {
            match &task.status {
                TaskStatus::Completed | TaskStatus::Failed(_) | TaskStatus::Cancelled => {
                    task.completed_at
                        .map(|t| t > cutoff)
                        .unwrap_or(task.created_at > cutoff)
                }
                _ => true, // Keep pending/in-progress tasks
            }
        });

        let removed = before - self.tasks.len();
        if removed > 0 {
            self.persistence.save_tasks(&self.tasks);
            info!("Cleaned {removed} old tasks");
        }
        removed
    }
}
