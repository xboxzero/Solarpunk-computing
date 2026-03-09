#!/usr/bin/env python3
"""
Solarpunk Web Terminal Gateway

Serves a mobile-friendly terminal UI over HTTP/WebSocket.
Any device on the network can open a browser to get a shell on the Pi.
Bridges browser WebSocket <-> local PTY shell.

Designed to handle heavy processes like Claude Code:
- Each session runs in its own process group for clean kill
- Large read buffers for fast CLI output
- Proper SIGKILL cleanup of entire process tree on disconnect
- Session tracking and watchdog for zombie prevention
- Ping/pong keepalive to detect dead connections
"""

import asyncio
import json
import os
import pty
import signal
import fcntl
import struct
import termios
import time

from aiohttp import web

HOST = "0.0.0.0"
PORT = 8822
MAX_SESSIONS = 4
READ_BUFFER = 16384     # 16KB reads for fast output (Claude is chatty)
PING_INTERVAL = 15      # WebSocket keepalive seconds
SESSION_TIMEOUT = 3600  # Kill sessions older than 1 hour with no WS


class Session:
    """Tracks a PTY shell session."""
    def __init__(self, pid, master_fd, ws):
        self.pid = pid
        self.master_fd = master_fd
        self.ws = ws
        self.created = time.time()
        self.last_activity = time.time()
        self.alive = True

    def touch(self):
        self.last_activity = time.time()


sessions = {}  # id -> Session


def kill_session(session):
    """Kill the entire process tree - ensures Claude + MCP servers all die."""
    if not session.alive:
        return
    session.alive = False
    pid = session.pid

    # Try killing the process group first, then the pid directly
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(pid), sig)
        except (OSError, ProcessLookupError):
            try:
                os.kill(pid, sig)
            except (OSError, ProcessLookupError):
                pass
        if sig == signal.SIGTERM:
            # Brief pause between TERM and KILL
            import time
            time.sleep(0.5)

    try:
        os.waitpid(pid, os.WNOHANG)
    except (OSError, ChildProcessError):
        pass

    try:
        os.close(session.master_fd)
    except OSError:
        pass


async def reap_zombies():
    """Periodically clean up dead sessions and zombie processes."""
    while True:
        await asyncio.sleep(30)
        now = time.time()
        dead = []
        for sid, session in sessions.items():
            # Check if process is still alive
            try:
                os.kill(session.pid, 0)
            except OSError:
                dead.append(sid)
                continue
            # Check for stale sessions
            if now - session.last_activity > SESSION_TIMEOUT:
                kill_session(session)
                dead.append(sid)
        for sid in dead:
            sessions.pop(sid, None)
        # Also reap any zombie children
        try:
            while True:
                pid, _ = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
        except ChildProcessError:
            pass


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
#top-bar .status.warn { color: #ff0; }
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
  scrollback: 5000,
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
let pingTimer;

function connect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws');
  ws.binaryType = 'arraybuffer';

  ws.onopen = () => {
    statusEl.textContent = 'connected';
    statusEl.className = 'status ok';
    const dims = JSON.stringify({type:'resize', cols:term.cols, rows:term.rows});
    ws.send(dims);
    // Keepalive ping
    if (pingTimer) clearInterval(pingTimer);
    pingTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({type:'ping'}));
      }
    }, 15000);
  };

  ws.onmessage = (e) => {
    if (e.data instanceof ArrayBuffer) {
      term.write(new Uint8Array(e.data));
    } else {
      // Check for server messages
      if (e.data.startsWith('{')) {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'pong') return;
          if (msg.type === 'error') {
            term.write('\\r\\n[server: ' + msg.message + ']\\r\\n');
            return;
          }
        } catch(ex) {}
      }
      term.write(e.data);
    }
  };

  ws.onclose = () => {
    statusEl.textContent = 'disconnected - reconnecting...';
    statusEl.className = 'status warn';
    if (pingTimer) clearInterval(pingTimer);
    reconnectTimer = setTimeout(connect, 2000);
  };

  ws.onerror = () => ws.close();
}

term.onData((data) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(data);
  }
});

function sendResize() {
  fitAddon.fit();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({type:'resize', cols:term.cols, rows:term.rows}));
  }
}

window.addEventListener('resize', sendResize);
screen.orientation && screen.orientation.addEventListener('change', () => setTimeout(sendResize, 200));

// Notify server before leaving so it can clean up
window.addEventListener('beforeunload', () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close(1000, 'page_unload');
  }
});

connect();
</script>
</body>
</html>"""


async def index(request):
    return web.Response(text=HTML, content_type="text/html")


async def health(request):
    """Health check + session list."""
    info = {
        "sessions": len(sessions),
        "max_sessions": MAX_SESSIONS,
        "uptime": int(time.time()),
    }
    for sid, s in sessions.items():
        info[f"session_{sid}"] = {
            "pid": s.pid,
            "alive": s.alive,
            "age": int(time.time() - s.created),
            "idle": int(time.time() - s.last_activity),
        }
    return web.json_response(info)


async def kill_all_sessions(request):
    """Emergency kill all sessions."""
    count = 0
    for sid, session in list(sessions.items()):
        kill_session(session)
        count += 1
    sessions.clear()
    return web.json_response({"killed": count})


async def websocket_handler(request):
    ws = web.WebSocketResponse(
        heartbeat=PING_INTERVAL,
        max_msg_size=64 * 1024,
    )
    await ws.prepare(request)

    # Check session limit
    active = sum(1 for s in sessions.values() if s.alive)
    if active >= MAX_SESSIONS:
        await ws.send_json({"type": "error", "message": f"max sessions ({MAX_SESSIONS}) reached"})
        await ws.close()
        return ws

    # Fork a PTY with its own process group
    pid, master_fd = pty.fork()
    if pid == 0:
        # Child: pty.fork() already calls setsid(), so we have our own session.
        # Just set a new process group for killpg() cleanup.
        try:
            os.setpgrp()
        except OSError:
            pass  # Already group leader from setsid
        os.environ["TERM"] = "xterm-256color"
        os.environ["COLUMNS"] = "80"
        os.environ["LINES"] = "24"
        project_dir = os.path.expanduser("~/Solarpunk-computing")
        if os.path.isdir(project_dir):
            os.chdir(project_dir)
        os.execvp("/bin/bash", ["/bin/bash", "--login"])

    # Parent: track session
    session = Session(pid, master_fd, ws)
    sid = id(session)
    sessions[sid] = session

    # Make master_fd non-blocking
    flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    loop = asyncio.get_running_loop()
    done = asyncio.Event()

    def on_pty_readable():
        try:
            data = os.read(master_fd, READ_BUFFER)
            if data:
                asyncio.ensure_future(ws.send_bytes(data))
                session.touch()
            else:
                done.set()
        except OSError:
            done.set()

    loop.add_reader(master_fd, on_pty_readable)

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
                            session.touch()
                            continue
                        if d.get("type") == "ping":
                            await ws.send_json({"type": "pong"})
                            session.touch()
                            continue
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
                try:
                    os.write(master_fd, text.encode())
                    session.touch()
                except OSError:
                    break
            elif msg.type == web.WSMsgType.BINARY:
                try:
                    os.write(master_fd, msg.data)
                    session.touch()
                except OSError:
                    break
            elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
                break
    finally:
        loop.remove_reader(master_fd)
        kill_session(session)
        sessions.pop(sid, None)

    return ws


def set_pty_size(fd, rows, cols):
    """Set PTY window size."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def main():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_get("/health", health)
    app.router.add_post("/kill", kill_all_sessions)

    # Start zombie reaper
    async def start_background(app):
        app["reaper"] = asyncio.create_task(reap_zombies())

    async def stop_background(app):
        app["reaper"].cancel()
        # Kill all sessions on shutdown
        for sid, session in list(sessions.items()):
            kill_session(session)
        sessions.clear()

    app.on_startup.append(start_background)
    app.on_cleanup.append(stop_background)

    print(f"Solarpunk Web Terminal on http://0.0.0.0:{PORT}")
    print(f"Open http://172.20.10.6:{PORT} from your iPhone")
    print(f"Max {MAX_SESSIONS} concurrent sessions, {READ_BUFFER}B buffer")
    web.run_app(app, host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
