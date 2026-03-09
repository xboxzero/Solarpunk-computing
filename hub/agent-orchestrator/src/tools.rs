use crate::types::{Tool, ToolResult};
use tracing::{debug, warn};

/// Execute a tool and return the result
pub async fn execute_tool(tool: &Tool) -> ToolResult {
    match tool {
        Tool::WebSearch { query } => web_search(query).await,
        Tool::WebFetch { url } => web_fetch(url).await,
        Tool::ShellExec { command } => shell_exec(command).await,
        Tool::FileRead { path } => file_read(path).await,
        Tool::FileWrite { path, content } => file_write(path, content).await,
        Tool::McpCall { server, tool: tool_name, args } => {
            mcp_call(server, tool_name, args).await
        }
        Tool::AgentMessage { target, message } => {
            // Handled by orchestrator, not here
            ToolResult {
                tool: "agent_message".into(),
                success: true,
                output: format!("Message queued for agent {target}: {message}"),
            }
        }
        Tool::CreateSubTask { title, description } => {
            // Handled by orchestrator
            ToolResult {
                tool: "create_subtask".into(),
                success: true,
                output: format!("Subtask created: {title}"),
            }
        }
    }
}

async fn web_search(query: &str) -> ToolResult {
    debug!("Web search: {query}");

    // Use DuckDuckGo HTML search (no API key needed)
    let client = reqwest::Client::new();
    let result = client
        .get("https://html.duckduckgo.com/html/")
        .query(&[("q", query)])
        .header("User-Agent", "SolarpunkAgent/0.1")
        .send()
        .await;

    match result {
        Ok(resp) => {
            let body = resp.text().await.unwrap_or_default();
            // Extract search result snippets from HTML
            let results = extract_search_results(&body);
            ToolResult {
                tool: "web_search".into(),
                success: true,
                output: if results.is_empty() {
                    format!("No results found for: {query}")
                } else {
                    results.join("\n\n")
                },
            }
        }
        Err(e) => ToolResult {
            tool: "web_search".into(),
            success: false,
            output: format!("Search failed: {e}"),
        },
    }
}

fn extract_search_results(html: &str) -> Vec<String> {
    let mut results = Vec::new();
    // Simple extraction: find result snippets between known markers
    // This is basic but functional without an HTML parser dependency
    for (i, chunk) in html.split("result__snippet").enumerate().skip(1) {
        if i > 5 { break; } // Top 5 results
        if let Some(start) = chunk.find('>') {
            let text = &chunk[start + 1..];
            if let Some(end) = text.find('<') {
                let snippet = text[..end]
                    .replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&quot;", "\"")
                    .replace("<b>", "")
                    .replace("</b>", "");
                let snippet = snippet.trim();
                if !snippet.is_empty() {
                    results.push(format!("[{i}] {snippet}"));
                }
            }
        }
    }
    results
}

async fn web_fetch(url: &str) -> ToolResult {
    debug!("Fetching URL: {url}");
    let client = reqwest::Client::new();
    match client
        .get(url)
        .header("User-Agent", "SolarpunkAgent/0.1")
        .send()
        .await
    {
        Ok(resp) => {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            // Truncate large responses
            let output = if body.len() > 10_000 {
                format!("{}\n... (truncated, {} bytes total)", &body[..10_000], body.len())
            } else {
                body
            };
            ToolResult {
                tool: "web_fetch".into(),
                success: status.is_success(),
                output,
            }
        }
        Err(e) => ToolResult {
            tool: "web_fetch".into(),
            success: false,
            output: format!("Fetch failed: {e}"),
        },
    }
}

async fn shell_exec(command: &str) -> ToolResult {
    debug!("Executing: {command}");

    // Safety: reject obviously dangerous commands
    let dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/sd"];
    for d in dangerous {
        if command.contains(d) {
            warn!("Blocked dangerous command: {command}");
            return ToolResult {
                tool: "shell_exec".into(),
                success: false,
                output: format!("Blocked: command contains dangerous pattern '{d}'"),
            };
        }
    }

    match tokio::process::Command::new("bash")
        .arg("-c")
        .arg(command)
        .output()
        .await
    {
        Ok(output) => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let stderr = String::from_utf8_lossy(&output.stderr);
            let combined = if stderr.is_empty() {
                stdout.to_string()
            } else {
                format!("{stdout}\nSTDERR: {stderr}")
            };
            ToolResult {
                tool: "shell_exec".into(),
                success: output.status.success(),
                output: combined,
            }
        }
        Err(e) => ToolResult {
            tool: "shell_exec".into(),
            success: false,
            output: format!("Exec failed: {e}"),
        },
    }
}

async fn file_read(path: &str) -> ToolResult {
    match tokio::fs::read_to_string(path).await {
        Ok(content) => ToolResult {
            tool: "file_read".into(),
            success: true,
            output: content,
        },
        Err(e) => ToolResult {
            tool: "file_read".into(),
            success: false,
            output: format!("Read failed: {e}"),
        },
    }
}

async fn file_write(path: &str, content: &str) -> ToolResult {
    match tokio::fs::write(path, content).await {
        Ok(()) => ToolResult {
            tool: "file_write".into(),
            success: true,
            output: format!("Written to {path}"),
        },
        Err(e) => ToolResult {
            tool: "file_write".into(),
            success: false,
            output: format!("Write failed: {e}"),
        },
    }
}

async fn mcp_call(server: &str, tool_name: &str, args: &serde_json::Value) -> ToolResult {
    debug!("MCP call: {server}/{tool_name}");

    // MCP over HTTP/SSE - send JSON-RPC request
    let client = reqwest::Client::new();
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args
        }
    });

    match client.post(server).json(&request).send().await {
        Ok(resp) => {
            let body = resp.text().await.unwrap_or_default();
            ToolResult {
                tool: format!("mcp:{tool_name}"),
                success: true,
                output: body,
            }
        }
        Err(e) => ToolResult {
            tool: format!("mcp:{tool_name}"),
            success: false,
            output: format!("MCP call failed: {e}"),
        },
    }
}
