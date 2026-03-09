use serde_json::Value;
use std::collections::HashMap;
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, ChildStdout, Command};
use tracing::{debug, info};

/// Info about a tool exposed by an MCP server
#[derive(Debug, Clone)]
pub struct McpToolInfo {
    pub name: String,
    pub description: String,
    pub input_schema: Value,
    pub server_name: String,
}

/// A single MCP stdio server connection
struct McpStdioClient {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
    next_id: u64,
    server_name: String,
    tools: Vec<McpToolInfo>,
}

impl McpStdioClient {
    async fn spawn(name: &str, command: &str, args: &[String]) -> Result<Self, String> {
        info!("Spawning MCP server '{name}': {command} {}", args.join(" "));

        let mut child = Command::new(command)
            .args(args)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn MCP server '{name}': {e}"))?;

        let stdin = child.stdin.take().ok_or("Failed to open stdin")?;
        let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
        let stdout = BufReader::new(stdout);

        let mut client = Self {
            child,
            stdin,
            stdout,
            next_id: 1,
            server_name: name.to_string(),
            tools: Vec::new(),
        };

        client.initialize().await?;
        client.discover_tools().await?;

        Ok(client)
    }

    /// Write a JSON-RPC message with Content-Length framing (LSP/MCP style)
    async fn write_message(&mut self, msg: &Value) -> Result<(), String> {
        let body = serde_json::to_string(msg).map_err(|e| e.to_string())?;
        let header = format!("Content-Length: {}\r\n\r\n", body.len());

        self.stdin
            .write_all(header.as_bytes())
            .await
            .map_err(|e| format!("Write header error: {e}"))?;
        self.stdin
            .write_all(body.as_bytes())
            .await
            .map_err(|e| format!("Write body error: {e}"))?;
        self.stdin
            .flush()
            .await
            .map_err(|e| format!("Flush error: {e}"))?;

        debug!("MCP [{name}] -> {body}", name = self.server_name);
        Ok(())
    }

    /// Read a JSON-RPC message with Content-Length framing
    async fn read_message(&mut self) -> Result<Value, String> {
        let mut content_length: Option<usize> = None;

        // Read headers
        loop {
            let mut line = String::new();
            self.stdout
                .read_line(&mut line)
                .await
                .map_err(|e| format!("Read header error: {e}"))?;

            let trimmed = line.trim();
            if trimmed.is_empty() {
                break;
            }
            if let Some(len_str) = trimmed.strip_prefix("Content-Length: ") {
                content_length = len_str.trim().parse().ok();
            }
        }

        let len = content_length.ok_or("Missing Content-Length header from MCP server")?;
        let mut buf = vec![0u8; len];
        self.stdout
            .read_exact(&mut buf)
            .await
            .map_err(|e| format!("Read body error: {e}"))?;

        let text = String::from_utf8(buf).map_err(|e| format!("UTF-8 error: {e}"))?;
        debug!("MCP [{name}] <- {text}", name = self.server_name);

        serde_json::from_str(&text).map_err(|e| format!("JSON parse error: {e}: {text}"))
    }

    /// Send a JSON-RPC request and wait for the response with matching ID
    async fn request(&mut self, method: &str, params: Value) -> Result<Value, String> {
        let id = self.next_id;
        self.next_id += 1;

        let msg = serde_json::json!({
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params,
        });

        self.write_message(&msg).await?;

        // Read responses until we get the one with our ID
        // (skip notifications)
        loop {
            let response = self.read_message().await?;

            // Check if it's a response (has id field)
            if let Some(resp_id) = response.get("id").and_then(|v| v.as_u64()) {
                if resp_id == id {
                    if let Some(error) = response.get("error") {
                        return Err(format!("MCP error: {error}"));
                    }
                    return Ok(response.get("result").cloned().unwrap_or(Value::Null));
                }
            }
            // Otherwise it's a notification — skip it
            debug!(
                "MCP [{name}] skipping notification: {response}",
                name = self.server_name
            );
        }
    }

    /// Send a JSON-RPC notification (no response expected)
    async fn notify(&mut self, method: &str, params: Value) -> Result<(), String> {
        let msg = serde_json::json!({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        });
        self.write_message(&msg).await
    }

    /// MCP initialize handshake
    async fn initialize(&mut self) -> Result<(), String> {
        let result = self
            .request(
                "initialize",
                serde_json::json!({
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "solarpunk-agent",
                        "version": env!("CARGO_PKG_VERSION")
                    }
                }),
            )
            .await?;

        info!(
            "MCP [{name}] initialized: {result}",
            name = self.server_name
        );

        // Send initialized notification
        self.notify("notifications/initialized", serde_json::json!({}))
            .await?;

        Ok(())
    }

    /// Discover tools from the MCP server
    async fn discover_tools(&mut self) -> Result<(), String> {
        let result = self.request("tools/list", serde_json::json!({})).await?;

        let tools_array = result
            .get("tools")
            .and_then(|t| t.as_array())
            .cloned()
            .unwrap_or_default();

        self.tools.clear();
        for tool in &tools_array {
            self.tools.push(McpToolInfo {
                name: tool
                    .get("name")
                    .and_then(|n| n.as_str())
                    .unwrap_or("")
                    .to_string(),
                description: tool
                    .get("description")
                    .and_then(|d| d.as_str())
                    .unwrap_or("")
                    .to_string(),
                input_schema: tool.get("inputSchema").cloned().unwrap_or(Value::Null),
                server_name: self.server_name.clone(),
            });
        }

        info!(
            "MCP [{name}] discovered {count} tools: {tools}",
            name = self.server_name,
            count = self.tools.len(),
            tools = self
                .tools
                .iter()
                .map(|t| t.name.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        );

        Ok(())
    }

    /// Call a tool on this MCP server
    async fn call_tool(&mut self, tool_name: &str, args: &Value) -> Result<String, String> {
        let result = self
            .request(
                "tools/call",
                serde_json::json!({
                    "name": tool_name,
                    "arguments": args,
                }),
            )
            .await?;

        // Extract text content from MCP response
        if let Some(content) = result.get("content").and_then(|c| c.as_array()) {
            let texts: Vec<&str> = content
                .iter()
                .filter_map(|c| c.get("text").and_then(|t| t.as_str()))
                .collect();
            if !texts.is_empty() {
                return Ok(texts.join("\n"));
            }
        }

        // Fall back to raw result
        Ok(serde_json::to_string_pretty(&result).unwrap_or_else(|_| result.to_string()))
    }

    async fn shutdown(&mut self) {
        info!("Shutting down MCP server '{}'", self.server_name);
        let _ = self.child.kill().await;
    }
}

/// Manages multiple MCP server connections
pub struct McpManager {
    servers: HashMap<String, McpStdioClient>,
}

impl McpManager {
    pub fn new() -> Self {
        Self {
            servers: HashMap::new(),
        }
    }

    /// Connect to an MCP server via stdio transport
    pub async fn connect_stdio(
        &mut self,
        name: &str,
        command: &str,
        args: &[String],
    ) -> Result<Vec<McpToolInfo>, String> {
        let client = McpStdioClient::spawn(name, command, args).await?;
        let tools = client.tools.clone();
        self.servers.insert(name.to_string(), client);
        Ok(tools)
    }

    /// Check if a server is connected
    pub fn has_server(&self, name: &str) -> bool {
        self.servers.contains_key(name)
    }

    /// List all connected servers
    pub fn list_servers(&self) -> Vec<(&str, usize)> {
        self.servers
            .iter()
            .map(|(name, client)| (name.as_str(), client.tools.len()))
            .collect()
    }

    /// Get all tools from all servers
    pub fn all_tools(&self) -> Vec<McpToolInfo> {
        self.servers
            .values()
            .flat_map(|c| c.tools.clone())
            .collect()
    }

    /// Get tools from a specific server
    pub fn server_tools(&self, name: &str) -> Vec<McpToolInfo> {
        self.servers
            .get(name)
            .map(|c| c.tools.clone())
            .unwrap_or_default()
    }

    /// Call a tool on a specific server
    pub async fn call_tool(
        &mut self,
        server: &str,
        tool_name: &str,
        args: &Value,
    ) -> Result<String, String> {
        let client = self
            .servers
            .get_mut(server)
            .ok_or_else(|| format!("MCP server '{server}' not connected"))?;

        client.call_tool(tool_name, args).await
    }

    /// Disconnect a server
    pub async fn disconnect(&mut self, name: &str) {
        if let Some(mut client) = self.servers.remove(name) {
            client.shutdown().await;
        }
    }

    /// Shutdown all servers
    pub async fn shutdown_all(&mut self) {
        let names: Vec<String> = self.servers.keys().cloned().collect();
        for name in names {
            self.disconnect(&name).await;
        }
    }
}
