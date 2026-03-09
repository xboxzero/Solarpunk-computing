#!/usr/bin/env python3
"""
Solarpunk Web Terminal Gateway

Serves a mobile-friendly terminal UI over HTTP/WebSocket.
Any device on the network can open a browser to get a shell on the Pi.
Bridges browser WebSocket <-> local PTY shell.
"""

import asyncio
import os
import pty
import signal
import fcntl
import struct
import termios

from aiohttp import web

HOST = "0.0.0.0"
PORT = 8822

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<title>Solarpunk Terminal</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/css/xterm.min.css">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background: #0a0a0a;
  overflow: hidden;
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
}
#top-bar {
  background: #1a1a2e;
  color: #0f0;
  padding: 6px 12px;
  font: bold 14px monospace;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}
#top-bar .status { font-size: 12px; color: #888; }
#top-bar .status.ok { color: #0f0; }
#terminal { flex: 1; }
</style>
</head>
<body>
<div id="top-bar">
  <span>solarpunk@xeropi2 ~/Solarpunk-computing</span>
  <span id="status" class="status">connecting...</span>
</div>
<div id="terminal"></div>

<script src="https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/lib/xterm.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/lib/addon-fit.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-web-links@0.11.0/lib/addon-web-links.min.js"></script>
<script>
const term = new Terminal({
  cursorBlink: true,
  fontSize: 15,
  fontFamily: 'Menlo, Monaco, Consolas, monospace',
  theme: {
    background: '#0a0a0a',
    foreground: '#e0e0e0',
    cursor: '#0f0',
    selectionBackground: '#333',
  },
  scrollback: 2000,
  convertEol: false,
  allowProposedApi: true,
});

const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.loadAddon(new WebLinksAddon.WebLinksAddon());
term.open(document.getElementById('terminal'));
fitAddon.fit();

const statusEl = document.getElementById('status');
let ws;
let reconnectTimer;

function connect() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws');
  ws.binaryType = 'arraybuffer';

  ws.onopen = () => {
    statusEl.textContent = 'connected';
    statusEl.className = 'status ok';
    // Send initial size
    const dims = JSON.stringify({type:'resize', cols:term.cols, rows:term.rows});
    ws.send(dims);
  };

  ws.onmessage = (e) => {
    if (e.data instanceof ArrayBuffer) {
      term.write(new Uint8Array(e.data));
    } else {
      term.write(e.data);
    }
  };

  ws.onclose = () => {
    statusEl.textContent = 'disconnected - reconnecting...';
    statusEl.className = 'status';
    reconnectTimer = setTimeout(connect, 2000);
  };

  ws.onerror = () => ws.close();
}

term.onData((data) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(data);
  }
});

window.addEventListener('resize', () => {
  fitAddon.fit();
  if (ws && ws.readyState === WebSocket.OPEN) {
    const dims = JSON.stringify({type:'resize', cols:term.cols, rows:term.rows});
    ws.send(dims);
  }
});

// Handle mobile orientation change
screen.orientation && screen.orientation.addEventListener('change', () => {
  setTimeout(() => {
    fitAddon.fit();
    if (ws && ws.readyState === WebSocket.OPEN) {
      const dims = JSON.stringify({type:'resize', cols:term.cols, rows:term.rows});
      ws.send(dims);
    }
  }, 200);
});

connect();
</script>
</body>
</html>"""


async def index(request):
    return web.Response(text=HTML, content_type="text/html")


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Fork a PTY in the Solarpunk project directory
    pid, master_fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.environ["COLUMNS"] = "80"
        os.environ["LINES"] = "24"
        project_dir = os.path.expanduser("~/Solarpunk-computing")
        if os.path.isdir(project_dir):
            os.chdir(project_dir)
        os.execvp("/bin/bash", ["/bin/bash", "--login"])

    # Make master_fd non-blocking
    flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    loop = asyncio.get_running_loop()
    done = asyncio.Event()

    def on_pty_readable():
        try:
            data = os.read(master_fd, 4096)
            if data:
                asyncio.ensure_future(ws.send_bytes(data))
            else:
                done.set()
        except OSError:
            done.set()

    loop.add_reader(master_fd, on_pty_readable)

    import json

    try:
        async for msg in ws:
            if done.is_set():
                break
            if msg.type == web.WSMsgType.TEXT:
                text = msg.data
                if text.startswith("{"):
                    try:
                        d = json.loads(text)
                        if d.get("type") == "resize":
                            set_pty_size(master_fd, d["rows"], d["cols"])
                            continue
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
                os.write(master_fd, text.encode())
            elif msg.type == web.WSMsgType.BINARY:
                os.write(master_fd, msg.data)
            elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
                break
    finally:
        loop.remove_reader(master_fd)
        try:
            os.kill(pid, signal.SIGTERM)
            os.waitpid(pid, 0)
        except (OSError, ChildProcessError):
            pass
        try:
            os.close(master_fd)
        except OSError:
            pass

    return ws


def set_pty_size(fd, rows, cols):
    """Set PTY window size."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def main():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/ws", websocket_handler)

    print(f"Solarpunk Web Terminal on http://0.0.0.0:{PORT}")
    print(f"Open http://172.20.10.6:{PORT} from your iPhone")
    web.run_app(app, host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
