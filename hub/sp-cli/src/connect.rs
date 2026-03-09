use crossterm::{
    event::{self, Event, KeyCode, KeyModifiers},
    terminal,
};
use futures_util::{SinkExt, StreamExt};
use std::io::Write;
use tokio_tungstenite::{connect_async, tungstenite::Message};

pub async fn run(host: &str, port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let url = format!("ws://{host}:{port}/ws");
    println!("Connecting to {url}...");

    let (ws_stream, _) = connect_async(&url).await?;
    let (mut ws_tx, mut ws_rx) = ws_stream.split();

    // Send initial resize
    let (cols, rows) = terminal::size().unwrap_or((80, 24));
    let resize_msg = serde_json::json!({"type": "resize", "cols": cols, "rows": rows});
    ws_tx
        .send(Message::Text(resize_msg.to_string().into()))
        .await?;

    println!("Connected. Press Ctrl+] to disconnect.\r\n");

    // Enter raw mode
    terminal::enable_raw_mode()?;

    let (shutdown_tx, mut shutdown_rx) = tokio::sync::oneshot::channel::<()>();
    let shutdown_tx = std::sync::Mutex::new(Some(shutdown_tx));

    // Stdin reader task
    let stdin_handle = tokio::task::spawn_blocking({
        let shutdown_tx = std::sync::Arc::new(shutdown_tx);
        move || {
            loop {
                if event::poll(std::time::Duration::from_millis(50)).unwrap_or(false) {
                    if let Ok(evt) = event::read() {
                        match evt {
                            Event::Key(key) => {
                                // Ctrl+] to disconnect
                                if key.modifiers.contains(KeyModifiers::CONTROL)
                                    && key.code == KeyCode::Char(']')
                                {
                                    if let Some(tx) = shutdown_tx.lock().unwrap().take() {
                                        let _ = tx.send(());
                                    }
                                    return Vec::new();
                                }
                                // Convert key event to bytes
                                let bytes = key_to_bytes(&key.code, &key.modifiers);
                                if !bytes.is_empty() {
                                    return bytes;
                                }
                            }
                            Event::Resize(cols, rows) => {
                                let msg = serde_json::json!({"type": "resize", "cols": cols, "rows": rows});
                                return msg.to_string().into_bytes();
                            }
                            _ => {}
                        }
                    }
                }
            }
        }
    });

    // Better approach: use a channel for stdin events
    let (input_tx, mut input_rx) = tokio::sync::mpsc::unbounded_channel::<Vec<u8>>();
    let (done_tx, done_rx) = tokio::sync::watch::channel(false);

    // Spawn stdin reader thread
    drop(stdin_handle); // cancel the earlier one
    let _stdin_thread = std::thread::spawn({
        let input_tx = input_tx.clone();
        let done_rx = done_rx.clone();
        move || {
            while !*done_rx.borrow() {
                if event::poll(std::time::Duration::from_millis(50)).unwrap_or(false) {
                    if let Ok(evt) = event::read() {
                        match evt {
                            Event::Key(key) => {
                                if key.modifiers.contains(KeyModifiers::CONTROL)
                                    && key.code == KeyCode::Char(']')
                                {
                                    break;
                                }
                                let bytes = key_to_bytes(&key.code, &key.modifiers);
                                if !bytes.is_empty() {
                                    if input_tx.send(bytes).is_err() {
                                        break;
                                    }
                                }
                            }
                            Event::Resize(cols, rows) => {
                                let msg = serde_json::json!({"type": "resize", "cols": cols, "rows": rows});
                                let _ = input_tx.send(msg.to_string().into_bytes());
                            }
                            _ => {}
                        }
                    }
                }
            }
            // Signal main loop to exit
            let _ = input_tx.send(vec![]);
        }
    });

    // Ping timer
    let mut ping_interval = tokio::time::interval(std::time::Duration::from_secs(15));
    ping_interval.tick().await; // skip first immediate tick

    let mut stdout = std::io::stdout();

    loop {
        tokio::select! {
            // Data from stdin
            Some(data) = input_rx.recv() => {
                if data.is_empty() {
                    break; // disconnect signal
                }
                let text: String = String::from_utf8_lossy(&data).into_owned();
                ws_tx.send(Message::Text(text.into())).await?;
            }
            // Data from WebSocket
            msg = ws_rx.next() => {
                match msg {
                    Some(Ok(Message::Binary(data))) => {
                        stdout.write_all(&data)?;
                        stdout.flush()?;
                    }
                    Some(Ok(Message::Text(text))) => {
                        // Check for JSON control messages
                        if text.starts_with('{') {
                            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&text) {
                                if val.get("type").and_then(|t| t.as_str()) == Some("pong") {
                                    continue;
                                }
                                if val.get("type").and_then(|t| t.as_str()) == Some("error") {
                                    let msg = val.get("message").and_then(|m| m.as_str()).unwrap_or("unknown error");
                                    eprintln!("\r\n[server error: {msg}]\r\n");
                                    continue;
                                }
                            }
                        }
                        stdout.write_all(text.as_bytes())?;
                        stdout.flush()?;
                    }
                    Some(Ok(Message::Close(_))) | None => {
                        break;
                    }
                    Some(Err(e)) => {
                        eprintln!("\r\nWebSocket error: {e}\r\n");
                        break;
                    }
                    _ => {}
                }
            }
            // Keepalive ping
            _ = ping_interval.tick() => {
                let ping = serde_json::json!({"type": "ping"});
                let _ = ws_tx.send(Message::Text(ping.to_string().into())).await;
            }
            // Shutdown signal
            _ = &mut shutdown_rx => {
                break;
            }
        }
    }

    // Cleanup
    let _ = done_tx.send(true);
    terminal::disable_raw_mode()?;
    println!("\r\nDisconnected.");

    Ok(())
}

fn key_to_bytes(code: &KeyCode, modifiers: &KeyModifiers) -> Vec<u8> {
    let ctrl = modifiers.contains(KeyModifiers::CONTROL);
    match code {
        KeyCode::Char(c) => {
            if ctrl {
                // Ctrl+A = 0x01, Ctrl+Z = 0x1A, etc.
                let byte = (*c as u8).wrapping_sub(b'a').wrapping_add(1);
                if byte <= 26 {
                    return vec![byte];
                }
            }
            let mut buf = [0u8; 4];
            let s = c.encode_utf8(&mut buf);
            s.as_bytes().to_vec()
        }
        KeyCode::Enter => vec![b'\r'],
        KeyCode::Backspace => vec![0x7f],
        KeyCode::Tab => vec![b'\t'],
        KeyCode::Esc => vec![0x1b],
        KeyCode::Up => b"\x1b[A".to_vec(),
        KeyCode::Down => b"\x1b[B".to_vec(),
        KeyCode::Right => b"\x1b[C".to_vec(),
        KeyCode::Left => b"\x1b[D".to_vec(),
        KeyCode::Home => b"\x1b[H".to_vec(),
        KeyCode::End => b"\x1b[F".to_vec(),
        KeyCode::PageUp => b"\x1b[5~".to_vec(),
        KeyCode::PageDown => b"\x1b[6~".to_vec(),
        KeyCode::Delete => b"\x1b[3~".to_vec(),
        KeyCode::Insert => b"\x1b[2~".to_vec(),
        KeyCode::F(n) => {
            match n {
                1 => b"\x1bOP".to_vec(),
                2 => b"\x1bOQ".to_vec(),
                3 => b"\x1bOR".to_vec(),
                4 => b"\x1bOS".to_vec(),
                5 => b"\x1b[15~".to_vec(),
                6 => b"\x1b[17~".to_vec(),
                7 => b"\x1b[18~".to_vec(),
                8 => b"\x1b[19~".to_vec(),
                9 => b"\x1b[20~".to_vec(),
                10 => b"\x1b[21~".to_vec(),
                11 => b"\x1b[23~".to_vec(),
                12 => b"\x1b[24~".to_vec(),
                _ => vec![],
            }
        }
        _ => vec![],
    }
}
