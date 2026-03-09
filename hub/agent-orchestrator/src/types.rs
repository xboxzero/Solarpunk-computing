use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Unique identifier for agents and tasks
pub type AgentId = Uuid;
pub type TaskId = Uuid;

/// What kind of LLM backend to use
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LlmBackend {
    /// Claude API (cloud)
    Claude { api_key: String, model: String },
    /// Local llama.cpp instance
    LocalLlama { endpoint: String, model: String },
    /// Any OpenAI-compatible API
    OpenAiCompat { endpoint: String, api_key: String, model: String },
}

/// Role/specialization of an agent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AgentRole {
    /// General purpose assistant
    General,
    /// Code writer & reviewer
    Coder,
    /// Internet researcher
    Researcher,
    /// System administrator / DevOps
    SysAdmin,
    /// Mesh network operator
    MeshOperator,
    /// Custom role with description
    Custom(String),
}

/// Current state of an agent
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AgentStatus {
    Idle,
    Working,
    WaitingForInput,
    Error(String),
    Shutdown,
}

/// A task that can be assigned to an agent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: TaskId,
    pub title: String,
    pub description: String,
    pub assigned_to: Option<AgentId>,
    pub status: TaskStatus,
    pub result: Option<String>,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub completed_at: Option<chrono::DateTime<chrono::Utc>>,
    pub parent_task: Option<TaskId>,
    pub subtasks: Vec<TaskId>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskStatus {
    Pending,
    InProgress,
    Completed,
    Failed(String),
    Cancelled,
}

/// A message in a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: MessageRole,
    pub content: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessageRole {
    System,
    User,
    Assistant,
    Tool { name: String, result: String },
}

/// MCP tool definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpTool {
    pub name: String,
    pub description: String,
    pub input_schema: serde_json::Value,
    pub server_url: String,
}

/// Available tools/capabilities for agents
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Tool {
    /// Search the web
    WebSearch { query: String },
    /// Fetch a URL
    WebFetch { url: String },
    /// Execute a shell command
    ShellExec { command: String },
    /// Read a file
    FileRead { path: String },
    /// Write a file
    FileWrite { path: String, content: String },
    /// Call an MCP tool
    McpCall { server: String, tool: String, args: serde_json::Value },
    /// Send message to another agent
    AgentMessage { target: AgentId, message: String },
    /// Create a sub-task
    CreateSubTask { title: String, description: String },
}

/// Result from a tool execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    pub tool: String,
    pub success: bool,
    pub output: String,
}

/// Configuration for the orchestrator
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestratorConfig {
    pub default_backend: LlmBackend,
    pub max_agents: usize,
    pub max_concurrent_tasks: usize,
    pub mcp_servers: Vec<McpServerConfig>,
    pub workspace_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpServerConfig {
    pub name: String,
    pub url: String,
    pub transport: McpTransport,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum McpTransport {
    Stdio { command: String, args: Vec<String> },
    Sse { url: String },
}
