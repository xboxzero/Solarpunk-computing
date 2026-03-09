use crate::agent::Agent;
use crate::types::*;
use chrono::Utc;
use std::collections::HashMap;
use tracing::{info, warn};
use uuid::Uuid;

/// The main orchestrator that manages multiple agents
pub struct Orchestrator {
    agents: HashMap<AgentId, Agent>,
    tasks: HashMap<TaskId, Task>,
    config: OrchestratorConfig,
}

impl Orchestrator {
    pub fn new(config: OrchestratorConfig) -> Self {
        info!("Orchestrator starting with max {} agents", config.max_agents);
        Self {
            agents: HashMap::new(),
            tasks: HashMap::new(),
            config,
        }
    }

    /// Spawn a new agent with a given role
    pub fn spawn_agent(&mut self, name: &str, role: AgentRole) -> Result<AgentId, String> {
        if self.agents.len() >= self.config.max_agents {
            return Err(format!(
                "Max agents reached ({}). Remove an agent first.",
                self.config.max_agents
            ));
        }

        let agent = Agent::new(name, role.clone(), self.config.default_backend.clone());
        let id = agent.id;
        info!("Spawned agent '{}' ({:?}) with id {}", name, role, id);
        self.agents.insert(id, agent);
        Ok(id)
    }

    /// Send a message to a specific agent
    pub async fn send_to_agent(&mut self, agent_id: &AgentId, message: &str) -> Result<String, String> {
        let agent = self
            .agents
            .get_mut(agent_id)
            .ok_or_else(|| format!("Agent {agent_id} not found"))?;

        agent.process(message).await
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
        self.tasks.insert(id, task);
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
            .map(|a| info!("Removed agent '{}' ({})", a.name, id))
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
                Ok(agent_id)
            }
            None => Err("No idle agents available".into()),
        }
    }
}
