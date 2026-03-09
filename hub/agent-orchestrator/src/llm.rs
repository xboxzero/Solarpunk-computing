use crate::types::{LlmBackend, Message, MessageRole};
use serde::{Deserialize, Serialize};
use tracing::{debug, error};

/// LLM client that supports multiple backends
pub struct LlmClient {
    http: reqwest::Client,
    backend: LlmBackend,
}

#[derive(Serialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: u32,
    messages: Vec<ClaudeMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    system: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct ClaudeMessage {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct ClaudeResponse {
    content: Vec<ClaudeContent>,
}

#[derive(Deserialize)]
struct ClaudeContent {
    text: String,
}

#[derive(Serialize)]
struct OpenAiRequest {
    model: String,
    messages: Vec<OpenAiMessage>,
    max_tokens: Option<u32>,
}

#[derive(Serialize, Deserialize)]
struct OpenAiMessage {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct OpenAiResponse {
    choices: Vec<OpenAiChoice>,
}

#[derive(Deserialize)]
struct OpenAiChoice {
    message: OpenAiMessage,
}

impl LlmClient {
    pub fn new(backend: LlmBackend) -> Self {
        Self {
            http: reqwest::Client::new(),
            backend,
        }
    }

    /// Send messages to the LLM and get a response
    pub async fn chat(&self, messages: &[Message], system_prompt: Option<&str>) -> Result<String, String> {
        match &self.backend {
            LlmBackend::Claude { api_key, model } => {
                self.chat_claude(api_key, model, messages, system_prompt).await
            }
            LlmBackend::ClaudeOAuth { access_token, model } => {
                self.chat_claude_oauth(access_token, model, messages, system_prompt).await
            }
            LlmBackend::LocalLlama { endpoint, model } => {
                self.chat_openai_compat(endpoint, "", model, messages, system_prompt).await
            }
            LlmBackend::OpenAiCompat { endpoint, api_key, model } => {
                self.chat_openai_compat(endpoint, api_key, model, messages, system_prompt).await
            }
        }
    }

    async fn chat_claude(
        &self,
        api_key: &str,
        model: &str,
        messages: &[Message],
        system_prompt: Option<&str>,
    ) -> Result<String, String> {
        let claude_messages: Vec<ClaudeMessage> = messages
            .iter()
            .filter_map(|m| {
                let role = match &m.role {
                    MessageRole::User => "user",
                    MessageRole::Assistant => "assistant",
                    MessageRole::System => return None,
                    MessageRole::Tool { .. } => "user",
                };
                Some(ClaudeMessage {
                    role: role.to_string(),
                    content: m.content.clone(),
                })
            })
            .collect();

        let request = ClaudeRequest {
            model: model.to_string(),
            max_tokens: 4096,
            messages: claude_messages,
            system: system_prompt.map(String::from),
        };

        debug!("Sending request to Claude API");

        let response = self
            .http
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&request)
            .send()
            .await
            .map_err(|e| format!("HTTP error: {e}"))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            error!("Claude API error {status}: {body}");
            return Err(format!("Claude API error {status}: {body}"));
        }

        let body: ClaudeResponse = response
            .json()
            .await
            .map_err(|e| format!("Parse error: {e}"))?;

        Ok(body.content.into_iter().map(|c| c.text).collect::<Vec<_>>().join(""))
    }

    async fn chat_claude_oauth(
        &self,
        access_token: &str,
        model: &str,
        messages: &[Message],
        system_prompt: Option<&str>,
    ) -> Result<String, String> {
        let claude_messages: Vec<ClaudeMessage> = messages
            .iter()
            .filter_map(|m| {
                let role = match &m.role {
                    MessageRole::User => "user",
                    MessageRole::Assistant => "assistant",
                    MessageRole::System => return None,
                    MessageRole::Tool { .. } => "user",
                };
                Some(ClaudeMessage {
                    role: role.to_string(),
                    content: m.content.clone(),
                })
            })
            .collect();

        let request = ClaudeRequest {
            model: model.to_string(),
            max_tokens: 4096,
            messages: claude_messages,
            system: system_prompt.map(String::from),
        };

        debug!("Sending request to Claude API via OAuth");

        let response = self
            .http
            .post("https://api.anthropic.com/v1/messages")
            .header("authorization", format!("Bearer {access_token}"))
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&request)
            .send()
            .await
            .map_err(|e| format!("HTTP error: {e}"))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            error!("Claude OAuth API error {status}: {body}");
            return Err(format!("Claude API error {status}: {body}"));
        }

        let body: ClaudeResponse = response
            .json()
            .await
            .map_err(|e| format!("Parse error: {e}"))?;

        Ok(body.content.into_iter().map(|c| c.text).collect::<Vec<_>>().join(""))
    }

    async fn chat_openai_compat(
        &self,
        endpoint: &str,
        api_key: &str,
        model: &str,
        messages: &[Message],
        system_prompt: Option<&str>,
    ) -> Result<String, String> {
        let mut oai_messages: Vec<OpenAiMessage> = Vec::new();

        if let Some(sys) = system_prompt {
            oai_messages.push(OpenAiMessage {
                role: "system".into(),
                content: sys.into(),
            });
        }

        for m in messages {
            let role = match &m.role {
                MessageRole::User => "user",
                MessageRole::Assistant => "assistant",
                MessageRole::System => "system",
                MessageRole::Tool { .. } => "user",
            };
            oai_messages.push(OpenAiMessage {
                role: role.to_string(),
                content: m.content.clone(),
            });
        }

        let request = OpenAiRequest {
            model: model.to_string(),
            messages: oai_messages,
            max_tokens: Some(4096),
        };

        let url = format!("{}/v1/chat/completions", endpoint.trim_end_matches('/'));
        debug!("Sending request to {url}");

        let mut req = self.http.post(&url).header("content-type", "application/json");
        if !api_key.is_empty() {
            req = req.header("authorization", format!("Bearer {api_key}"));
        }

        let response = req
            .json(&request)
            .send()
            .await
            .map_err(|e| format!("HTTP error: {e}"))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            return Err(format!("LLM API error {status}: {body}"));
        }

        let body: OpenAiResponse = response
            .json()
            .await
            .map_err(|e| format!("Parse error: {e}"))?;

        body.choices
            .first()
            .map(|c| c.message.content.clone())
            .ok_or_else(|| "No response from LLM".into())
    }
}
