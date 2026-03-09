use crate::llm::LlmClient;
use crate::tools;
use crate::types::*;
use chrono::Utc;
use tracing::{debug, info, error};
use uuid::Uuid;

/// A single AI agent worker
pub struct Agent {
    pub id: AgentId,
    pub name: String,
    pub role: AgentRole,
    pub status: AgentStatus,
    llm: LlmClient,
    conversation: Vec<Message>,
    system_prompt: String,
    available_tools: Vec<String>,
}

impl Agent {
    pub fn new(name: &str, role: AgentRole, backend: LlmBackend) -> Self {
        let system_prompt = build_system_prompt(&role);
        Self {
            id: Uuid::new_v4(),
            name: name.to_string(),
            role,
            status: AgentStatus::Idle,
            llm: LlmClient::new(backend),
            conversation: Vec::new(),
            system_prompt,
            available_tools: vec![
                "web_search".into(),
                "web_fetch".into(),
                "shell_exec".into(),
                "file_read".into(),
                "file_write".into(),
                "mcp_call".into(),
                "agent_message".into(),
                "create_subtask".into(),
            ],
        }
    }

    /// Process a user message and return agent's response
    pub async fn process(&mut self, input: &str) -> Result<String, String> {
        self.status = AgentStatus::Working;

        self.conversation.push(Message {
            role: MessageRole::User,
            content: input.to_string(),
            timestamp: Utc::now(),
        });

        // Agent loop: LLM thinks -> optionally uses tools -> responds
        let mut iterations = 0;
        let max_iterations = 10;

        loop {
            iterations += 1;
            if iterations > max_iterations {
                self.status = AgentStatus::Idle;
                return Err("Agent exceeded max iterations".into());
            }

            let response = self
                .llm
                .chat(&self.conversation, Some(&self.system_prompt))
                .await?;

            debug!("Agent {} response: {}", self.name, &response[..response.len().min(200)]);

            // Check if the response contains a tool call (JSON block)
            if let Some(tool_call) = parse_tool_call(&response) {
                info!("Agent {} calling tool: {}", self.name, tool_call.tool_name());

                // Execute the tool
                let result = tools::execute_tool(&tool_call).await;

                // Add assistant response + tool result to conversation
                self.conversation.push(Message {
                    role: MessageRole::Assistant,
                    content: response.clone(),
                    timestamp: Utc::now(),
                });
                self.conversation.push(Message {
                    role: MessageRole::Tool {
                        name: result.tool.clone(),
                        result: result.output.clone(),
                    },
                    content: format!(
                        "Tool '{}' result (success={}):\n{}",
                        result.tool, result.success, result.output
                    ),
                    timestamp: Utc::now(),
                });

                // Continue the loop so LLM can process tool result
                continue;
            }

            // No tool call — this is the final response
            self.conversation.push(Message {
                role: MessageRole::Assistant,
                content: response.clone(),
                timestamp: Utc::now(),
            });

            self.status = AgentStatus::Idle;
            return Ok(response);
        }
    }

    /// Get conversation history
    pub fn history(&self) -> &[Message] {
        &self.conversation
    }

    /// Reset conversation
    pub fn reset(&mut self) {
        self.conversation.clear();
        self.status = AgentStatus::Idle;
    }
}

fn build_system_prompt(role: &AgentRole) -> String {
    let role_desc = match role {
        AgentRole::General => "You are a helpful general-purpose AI assistant.",
        AgentRole::Coder => "You are an expert programmer. Write clean, efficient code.",
        AgentRole::Researcher => "You are a research specialist. Search the web and synthesize information thoroughly.",
        AgentRole::SysAdmin => "You are a Linux system administrator. Manage systems safely and efficiently.",
        AgentRole::MeshOperator => "You are a mesh network operator for a Solarpunk computing network. Monitor and manage ESP32 mesh nodes.",
        AgentRole::Custom(desc) => desc,
    };

    format!(
        r#"{role_desc}

You have access to tools. To use a tool, include a JSON block in your response:
```tool
{{"tool": "tool_name", "args": {{...}}}}
```

Available tools:
- web_search: Search the internet. Args: {{"query": "search terms"}}
- web_fetch: Fetch a URL. Args: {{"url": "https://..."}}
- shell_exec: Run a shell command. Args: {{"command": "ls -la"}}
- file_read: Read a file. Args: {{"path": "/path/to/file"}}
- file_write: Write a file. Args: {{"path": "/path/to/file", "content": "..."}}
- mcp_call: Call an MCP server tool. Args: {{"server": "url", "tool": "name", "args": {{...}}}}
- agent_message: Message another agent. Args: {{"target": "agent-id", "message": "..."}}
- create_subtask: Create a subtask. Args: {{"title": "...", "description": "..."}}

After using a tool, you'll receive the result and can continue reasoning.
When you have a final answer, respond normally without a tool block."#
    )
}

/// Parse a tool call from LLM response
fn parse_tool_call(response: &str) -> Option<Tool> {
    // Look for ```tool ... ``` blocks
    let start = response.find("```tool")?;
    let after_marker = &response[start + 7..];
    let end = after_marker.find("```")?;
    let json_str = after_marker[..end].trim();

    let parsed: serde_json::Value = serde_json::from_str(json_str).ok()?;
    let tool_name = parsed.get("tool")?.as_str()?;
    let args = parsed.get("args").cloned().unwrap_or(serde_json::Value::Null);

    match tool_name {
        "web_search" => Some(Tool::WebSearch {
            query: args.get("query")?.as_str()?.to_string(),
        }),
        "web_fetch" => Some(Tool::WebFetch {
            url: args.get("url")?.as_str()?.to_string(),
        }),
        "shell_exec" => Some(Tool::ShellExec {
            command: args.get("command")?.as_str()?.to_string(),
        }),
        "file_read" => Some(Tool::FileRead {
            path: args.get("path")?.as_str()?.to_string(),
        }),
        "file_write" => Some(Tool::FileWrite {
            path: args.get("path")?.as_str()?.to_string(),
            content: args.get("content")?.as_str()?.to_string(),
        }),
        "mcp_call" => Some(Tool::McpCall {
            server: args.get("server")?.as_str()?.to_string(),
            tool: args.get("tool")?.as_str()?.to_string(),
            args: args.get("args")?.clone(),
        }),
        _ => None,
    }
}

impl Tool {
    pub fn tool_name(&self) -> &str {
        match self {
            Tool::WebSearch { .. } => "web_search",
            Tool::WebFetch { .. } => "web_fetch",
            Tool::ShellExec { .. } => "shell_exec",
            Tool::FileRead { .. } => "file_read",
            Tool::FileWrite { .. } => "file_write",
            Tool::McpCall { .. } => "mcp_call",
            Tool::AgentMessage { .. } => "agent_message",
            Tool::CreateSubTask { .. } => "create_subtask",
        }
    }
}
