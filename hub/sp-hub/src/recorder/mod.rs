use axum::{
    Router,
    extract::{DefaultBodyLimit, Multipart},
    http::StatusCode,
    response::{Html, IntoResponse, Json},
    routing::{get, post},
};
use serde_json::json;

const MAX_UPLOAD_BYTES: usize = 50 * 1024 * 1024;
const WHISPER_URL: &str = "https://api.openai.com/v1/audio/transcriptions";

pub fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/health", get(health))
        .route("/transcribe", post(transcribe))
        .layer(DefaultBodyLimit::max(MAX_UPLOAD_BYTES))
}

async fn index() -> Html<&'static str> {
    Html(include_str!("../../static/recorder.html"))
}

async fn health() -> Json<serde_json::Value> {
    let key_set = std::env::var("OPENAI_API_KEY")
        .map(|k| !k.is_empty())
        .unwrap_or(false);
    Json(json!({
        "ok": true,
        "whisper_configured": key_set,
        "max_upload_bytes": MAX_UPLOAD_BYTES,
    }))
}

async fn transcribe(mut multipart: Multipart) -> axum::response::Response {
    let api_key = match std::env::var("OPENAI_API_KEY") {
        Ok(k) if !k.is_empty() => k,
        _ => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({
                    "error": "OPENAI_API_KEY is not set on the server. Set it in the sp-hub environment and restart to enable Whisper transcription."
                })),
            )
                .into_response();
        }
    };

    let mut audio_bytes: Option<Vec<u8>> = None;
    let mut filename = String::from("audio.webm");
    let mut model = String::from("whisper-1");
    let mut language: Option<String> = None;

    loop {
        let field = match multipart.next_field().await {
            Ok(Some(f)) => f,
            Ok(None) => break,
            Err(e) => {
                return (
                    StatusCode::BAD_REQUEST,
                    Json(json!({"error": format!("multipart read failed: {e}")})),
                )
                    .into_response();
            }
        };

        let name = field.name().unwrap_or("").to_string();
        match name.as_str() {
            "file" => {
                if let Some(fname) = field.file_name() {
                    filename = fname.to_string();
                }
                match field.bytes().await {
                    Ok(b) => audio_bytes = Some(b.to_vec()),
                    Err(e) => {
                        return (
                            StatusCode::BAD_REQUEST,
                            Json(json!({"error": format!("audio read failed: {e}")})),
                        )
                            .into_response();
                    }
                }
            }
            "model" => {
                if let Ok(v) = field.text().await {
                    if !v.is_empty() {
                        model = v;
                    }
                }
            }
            "language" => {
                if let Ok(v) = field.text().await {
                    if !v.is_empty() {
                        language = Some(v);
                    }
                }
            }
            _ => {
                let _ = field.bytes().await;
            }
        }
    }

    let bytes = match audio_bytes {
        Some(b) if !b.is_empty() => b,
        _ => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({"error": "no audio file in request"})),
            )
                .into_response();
        }
    };

    tracing::info!("transcribe: {} bytes, model={}, lang={:?}", bytes.len(), model, language);

    let part = match reqwest::multipart::Part::bytes(bytes).file_name(filename).mime_str("application/octet-stream") {
        Ok(p) => p,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"error": format!("multipart part build failed: {e}")})),
            )
                .into_response();
        }
    };

    let mut form = reqwest::multipart::Form::new()
        .text("model", model)
        .text("response_format", "verbose_json")
        .part("file", part);
    if let Some(lang) = language {
        form = form.text("language", lang);
    }

    let client = reqwest::Client::new();
    let resp = match client
        .post(WHISPER_URL)
        .bearer_auth(api_key)
        .multipart(form)
        .send()
        .await
    {
        Ok(r) => r,
        Err(e) => {
            return (
                StatusCode::BAD_GATEWAY,
                Json(json!({"error": format!("openai request failed: {e}")})),
            )
                .into_response();
        }
    };

    let status = resp.status();
    let body = resp.text().await.unwrap_or_default();
    if !status.is_success() {
        return (
            StatusCode::BAD_GATEWAY,
            Json(json!({"error": format!("openai {}: {}", status.as_u16(), body)})),
        )
            .into_response();
    }

    match serde_json::from_str::<serde_json::Value>(&body) {
        Ok(v) => Json(v).into_response(),
        Err(_) => Json(json!({"text": body.trim()})).into_response(),
    }
}
