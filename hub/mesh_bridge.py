#!/usr/bin/env python3
"""
Solarpunk Mesh-to-Reticulum Bridge

Runs on the Pi. Bridges ESP32 mesh nodes into the Reticulum network:
- Polls ESP32 nodes via HTTP API for mesh state (peers, status, messages)
- Announces each discovered mesh node as a Reticulum destination
- Relays messages between Reticulum peers and ESP32 mesh
- Provides a web dashboard showing full network topology

ESP32 nodes connect to Pi via WiFi STA ("solarpunk-pi" network).
Pi sees them on the 10.42.0.x subnet.
"""

import asyncio
import json
import os
import struct
import sys
import time
import threading

import RNS
import aiohttp
from aiohttp import web

# --- Configuration ---
BRIDGE_NAME = "solarpunk"
BRIDGE_ASPECT = "mesh"
POLL_INTERVAL = 5          # seconds between ESP32 polls
ESP32_SUBNET = "10.42.0"   # Pi hotspot subnet
ESP32_PORT = 80             # ESP32 web server port
AUTH_TOKEN = "solarpunk2026"
WEB_PORT = 8833            # Bridge dashboard port
ANNOUNCE_INTERVAL = 120    # Reticulum re-announce seconds


class MeshNode:
    """Represents a discovered ESP32 mesh node."""
    def __init__(self, ip, name, mac):
        self.ip = ip
        self.name = name
        self.mac = mac
        self.battery = 0
        self.solar_mv = 0
        self.peers = []
        self.peer_count = 0
        self.rssi = 0
        self.uptime = 0
        self.version = ""
        self.encrypted = False
        self.last_seen = time.time()
        self.online = True
        self.rns_destination = None

    @property
    def url(self):
        return f"http://{self.ip}:{ESP32_PORT}"

    def to_dict(self):
        return {
            "name": self.name,
            "ip": self.ip,
            "mac": self.mac,
            "battery": self.battery,
            "solar_mv": self.solar_mv,
            "peer_count": self.peer_count,
            "peers": self.peers,
            "uptime": self.uptime,
            "version": self.version,
            "encrypted": self.encrypted,
            "online": self.online,
            "last_seen": int(self.last_seen),
        }


class MeshBridge:
    """Bridges ESP32 mesh <-> Reticulum network."""

    def __init__(self):
        self.nodes = {}          # ip -> MeshNode
        self.mesh_peers = {}     # name -> peer info (from all nodes)
        self.messages = []       # recent mesh messages
        self.ws_clients = set()  # connected WebSocket clients
        self.running = False

        # Reticulum setup
        self.reticulum = RNS.Reticulum()
        self.identity = self._load_or_create_identity()

        # Main bridge destination
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            BRIDGE_NAME,
            BRIDGE_ASPECT,
        )
        self.destination.set_link_established_callback(self.on_rns_link)

        RNS.log(f"Mesh bridge started", RNS.LOG_NOTICE)
        RNS.log(f"Destination: {RNS.prettyhexrep(self.destination.hash)}", RNS.LOG_NOTICE)

    def _load_or_create_identity(self):
        id_path = os.path.expanduser("~/.reticulum/mesh_bridge_identity")
        if os.path.exists(id_path):
            return RNS.Identity.from_file(id_path)
        identity = RNS.Identity()
        identity.to_file(id_path)
        return identity

    def on_rns_link(self, link):
        """Handle incoming Reticulum link - provide mesh data."""
        link.set_link_closed_callback(self.on_rns_link_closed)
        channel = link.get_channel()
        channel.register_message_type(MeshQuery)
        channel.register_message_type(MeshResponse)
        channel.register_message_type(MeshCommand)
        channel.add_message_handler(lambda msg: self.on_rns_message(msg, channel))
        RNS.log(f"Reticulum peer connected: {RNS.prettyhexrep(link.hash)}", RNS.LOG_NOTICE)

    def on_rns_link_closed(self, link):
        RNS.log(f"Reticulum peer disconnected: {RNS.prettyhexrep(link.hash)}", RNS.LOG_INFO)

    def on_rns_message(self, message, channel):
        """Handle queries from Reticulum peers."""
        if isinstance(message, MeshQuery):
            # Return full mesh state
            state = {
                "nodes": {ip: n.to_dict() for ip, n in self.nodes.items()},
                "peers": self.mesh_peers,
                "bridge": RNS.prettyhexrep(self.destination.hash),
            }
            resp = MeshResponse(json.dumps(state).encode())
            channel.send(resp)
            return True
        elif isinstance(message, MeshCommand):
            # Forward command to an ESP32 node
            try:
                cmd = json.loads(message.data.decode())
                node_ip = cmd.get("node")
                command = cmd.get("cmd", "")
                if node_ip in self.nodes:
                    asyncio.run_coroutine_threadsafe(
                        self._send_command(node_ip, command, channel),
                        self.loop,
                    )
            except (json.JSONDecodeError, KeyError):
                pass
            return True
        return False

    async def _send_command(self, node_ip, command, channel):
        """Send a command to an ESP32 node and relay the result back."""
        node = self.nodes.get(node_ip)
        if not node:
            return
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{node.url}/api/run?token={AUTH_TOKEN}"
                async with session.post(url, data=command, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.text()
                    msg = MeshResponse(json.dumps({
                        "type": "exec_result",
                        "node": node.name,
                        "result": result,
                    }).encode())
                    channel.send(msg)
        except Exception as e:
            RNS.log(f"Command relay failed: {e}", RNS.LOG_WARNING)

    async def discover_nodes(self):
        """Scan the Pi hotspot subnet for ESP32 nodes."""
        tasks = []
        for i in range(2, 20):  # 10.42.0.2 through 10.42.0.19
            ip = f"{ESP32_SUBNET}.{i}"
            tasks.append(self._probe_node(ip))
        await asyncio.gather(*tasks)

    async def _probe_node(self, ip):
        """Try to contact an ESP32 node at this IP."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{ip}:{ESP32_PORT}/api/status"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        name = data.get("node", f"unknown-{ip}")
                        mac = data.get("mac", "")
                        if ip not in self.nodes:
                            self.nodes[ip] = MeshNode(ip, name, mac)
                            RNS.log(f"Discovered node: {name} at {ip}", RNS.LOG_NOTICE)
                        node = self.nodes[ip]
                        node.name = name
                        node.mac = mac
                        node.battery = data.get("battery", 0)
                        node.solar_mv = data.get("solar_mv", 0)
                        node.peer_count = data.get("peers", 0)
                        node.uptime = data.get("uptime", 0)
                        node.version = data.get("version", "")
                        node.encrypted = data.get("encrypted", False)
                        node.online = True
                        node.last_seen = time.time()
        except Exception:
            # Node not reachable at this IP
            if ip in self.nodes:
                if time.time() - self.nodes[ip].last_seen > 60:
                    self.nodes[ip].online = False

    async def poll_mesh_peers(self):
        """Get mesh peer tables from all known nodes."""
        for ip, node in list(self.nodes.items()):
            if not node.online:
                continue
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{node.url}/api/mesh/peers"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                        if resp.status == 200:
                            peers = await resp.json()
                            node.peers = peers if isinstance(peers, list) else []
                            for p in node.peers:
                                pname = p.get("name", "")
                                if pname:
                                    self.mesh_peers[pname] = {
                                        **p,
                                        "seen_by": node.name,
                                        "timestamp": int(time.time()),
                                    }
            except Exception:
                pass

    async def poll_loop(self):
        """Main polling loop."""
        while self.running:
            await self.discover_nodes()
            await self.poll_mesh_peers()
            await self.broadcast_state()
            await asyncio.sleep(POLL_INTERVAL)

    async def announce_loop(self):
        """Periodically re-announce on Reticulum."""
        while self.running:
            self.destination.announce()
            RNS.log(f"Announced. Nodes: {len(self.nodes)}, Mesh peers: {len(self.mesh_peers)}", RNS.LOG_INFO)
            await asyncio.sleep(ANNOUNCE_INTERVAL)

    async def broadcast_state(self):
        """Push state updates to connected WebSocket clients."""
        if not self.ws_clients:
            return
        state = json.dumps({
            "type": "state",
            "nodes": {ip: n.to_dict() for ip, n in self.nodes.items()},
            "peers": self.mesh_peers,
            "timestamp": int(time.time()),
        })
        dead = set()
        for ws in self.ws_clients:
            try:
                await ws.send_str(state)
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead

    # --- Web Dashboard ---

    def create_web_app(self):
        app = web.Application()
        app.router.add_get("/", self.handle_dashboard)
        app.router.add_get("/api/state", self.handle_api_state)
        app.router.add_post("/api/cmd", self.handle_api_cmd)
        app.router.add_get("/ws", self.handle_ws)
        return app

    async def handle_dashboard(self, request):
        return web.Response(text=DASHBOARD_HTML, content_type="text/html")

    async def handle_api_state(self, request):
        state = {
            "nodes": {ip: n.to_dict() for ip, n in self.nodes.items()},
            "peers": self.mesh_peers,
            "bridge_hash": RNS.prettyhexrep(self.destination.hash),
        }
        return web.json_response(state)

    async def handle_api_cmd(self, request):
        """Send a command to an ESP32 node."""
        try:
            body = await request.json()
            node_ip = body.get("node")
            command = body.get("cmd", "")
            if node_ip not in self.nodes:
                return web.json_response({"error": "node not found"}, status=404)
            node = self.nodes[node_ip]
            async with aiohttp.ClientSession() as session:
                url = f"{node.url}/api/run?token={AUTH_TOKEN}"
                async with session.post(url, data=command, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.text()
                    return web.json_response({"node": node.name, "result": result})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_ws(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    # Client can send commands
                    try:
                        data = json.loads(msg.data)
                        if data.get("type") == "cmd":
                            node_ip = data.get("node")
                            cmd = data.get("cmd", "")
                            if node_ip in self.nodes:
                                await self._send_ws_command(ws, node_ip, cmd)
                    except json.JSONDecodeError:
                        pass
                elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
                    break
        finally:
            self.ws_clients.discard(ws)
        return ws

    async def _send_ws_command(self, ws, node_ip, command):
        node = self.nodes.get(node_ip)
        if not node:
            return
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{node.url}/api/run?token={AUTH_TOKEN}"
                async with session.post(url, data=command, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.text()
                    await ws.send_str(json.dumps({
                        "type": "result",
                        "node": node.name,
                        "result": result,
                    }))
        except Exception as e:
            await ws.send_str(json.dumps({"type": "error", "error": str(e)}))

    async def run(self):
        self.running = True
        self.loop = asyncio.get_running_loop()

        # Start web dashboard
        app = self.create_web_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEB_PORT)
        await site.start()
        RNS.log(f"Dashboard on http://0.0.0.0:{WEB_PORT}", RNS.LOG_NOTICE)

        # Run poll + announce loops
        await asyncio.gather(
            self.poll_loop(),
            self.announce_loop(),
        )


# --- Reticulum Message Types ---

class MeshQuery(RNS.MessageBase):
    """Request mesh state from bridge."""
    MSGTYPE = 0x10
    def __init__(self, data=None):
        self.data = data or b""
    def pack(self):
        return self.data
    def unpack(self, raw):
        self.data = raw


class MeshResponse(RNS.MessageBase):
    """Mesh state response."""
    MSGTYPE = 0x11
    def __init__(self, data=None):
        self.data = data or b""
    def pack(self):
        return self.data
    def unpack(self, raw):
        self.data = raw


class MeshCommand(RNS.MessageBase):
    """Send command to mesh node via bridge."""
    MSGTYPE = 0x12
    def __init__(self, data=None):
        self.data = data or b""
    def pack(self):
        return self.data
    def unpack(self, raw):
        self.data = raw


# --- Dashboard HTML ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Solarpunk Mesh Bridge</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background: #0a0a0a; color: #e0e0e0;
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 14px; padding: 12px;
}
h1 { color: #0f0; font-size: 18px; margin-bottom: 8px; }
h2 { color: #0af; font-size: 15px; margin: 16px 0 8px; }
.meta { color: #666; font-size: 12px; margin-bottom: 16px; }
.status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.status.on { background: #0f0; }
.status.off { background: #f00; }
.node {
  background: #111; border: 1px solid #222; border-radius: 6px;
  padding: 12px; margin-bottom: 10px;
}
.node-name { color: #0f0; font-weight: bold; font-size: 15px; }
.node-ip { color: #666; font-size: 12px; }
.stat { display: inline-block; margin-right: 16px; margin-top: 4px; }
.stat label { color: #888; }
.stat value { color: #fff; }
.peer {
  background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 4px;
  padding: 8px; margin: 4px 0; font-size: 13px;
}
.peer-name { color: #ff0; }
.cmd-box {
  display: flex; gap: 8px; margin-top: 8px;
}
.cmd-box input {
  flex: 1; background: #111; border: 1px solid #333; color: #fff;
  padding: 6px 10px; border-radius: 4px; font-family: inherit; font-size: 13px;
}
.cmd-box button {
  background: #1a3a1a; color: #0f0; border: 1px solid #0f0;
  padding: 6px 14px; border-radius: 4px; cursor: pointer; font-family: inherit;
}
.cmd-box button:active { background: #0f0; color: #000; }
#result {
  background: #111; border: 1px solid #222; border-radius: 4px;
  padding: 8px; margin-top: 8px; white-space: pre-wrap;
  font-size: 13px; max-height: 200px; overflow-y: auto; display: none;
}
.topo {
  background: #111; border: 1px solid #222; border-radius: 6px;
  padding: 16px; margin-top: 12px; min-height: 80px;
}
.topo-node { display: inline-block; text-align: center; margin: 8px 12px; }
.topo-icon { font-size: 28px; }
.topo-label { font-size: 11px; color: #888; margin-top: 2px; }
.topo-line { color: #333; }
#ws-status { font-size: 11px; }
</style>
</head>
<body>

<h1>// solarpunk mesh bridge</h1>
<div class="meta">
  Pi gateway | Reticulum + ESP-NOW mesh |
  <span id="ws-status" style="color:#f00">connecting...</span>
</div>

<h2>-- topology --</h2>
<div class="topo" id="topo">scanning...</div>

<h2>-- esp32 nodes --</h2>
<div id="nodes">scanning subnet...</div>

<h2>-- mesh peers --</h2>
<div id="peers">waiting for data...</div>

<h2>-- command --</h2>
<div class="cmd-box">
  <select id="cmd-node" style="background:#111;color:#fff;border:1px solid #333;padding:6px;border-radius:4px;font-family:inherit;">
    <option value="">select node</option>
  </select>
  <input id="cmd-input" placeholder="status / peers / help" />
  <button onclick="sendCmd()">run</button>
</div>
<div id="result"></div>

<script>
let state = {};
const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
let ws;

function connect() {
  ws = new WebSocket(proto + '//' + location.host + '/ws');
  const statusEl = document.getElementById('ws-status');

  ws.onopen = () => { statusEl.style.color = '#0f0'; statusEl.textContent = 'live'; };
  ws.onclose = () => { statusEl.style.color = '#f00'; statusEl.textContent = 'reconnecting...'; setTimeout(connect, 2000); };
  ws.onerror = () => ws.close();

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'state') {
      state = msg;
      render();
    } else if (msg.type === 'result') {
      const el = document.getElementById('result');
      el.style.display = 'block';
      el.textContent = msg.node + '> ' + msg.result;
    } else if (msg.type === 'error') {
      const el = document.getElementById('result');
      el.style.display = 'block';
      el.textContent = 'ERROR: ' + msg.error;
    }
  };
}

function render() {
  // Nodes
  const nodesEl = document.getElementById('nodes');
  const nodes = state.nodes || {};
  const ips = Object.keys(nodes);
  if (ips.length === 0) {
    nodesEl.innerHTML = '<div style="color:#666">no nodes found yet...</div>';
  } else {
    nodesEl.innerHTML = ips.map(ip => {
      const n = nodes[ip];
      return `<div class="node">
        <span class="status ${n.online ? 'on' : 'off'}"></span>
        <span class="node-name">${n.name}</span>
        <span class="node-ip">${ip}</span>
        <br>
        <span class="stat"><label>bat </label><value>${n.battery}%</value></span>
        <span class="stat"><label>solar </label><value>${n.solar_mv}mV</value></span>
        <span class="stat"><label>peers </label><value>${n.peer_count}</value></span>
        <span class="stat"><label>up </label><value>${formatUptime(n.uptime)}</value></span>
        <span class="stat"><label>fw </label><value>${n.version}</value></span>
        <span class="stat"><label>enc </label><value>${n.encrypted ? 'AES-256' : 'off'}</value></span>
      </div>`;
    }).join('');
  }

  // Update node selector
  const sel = document.getElementById('cmd-node');
  const prev = sel.value;
  sel.innerHTML = '<option value="">select node</option>' +
    ips.filter(ip => nodes[ip].online).map(ip =>
      `<option value="${ip}">${nodes[ip].name} (${ip})</option>`
    ).join('');
  sel.value = prev;

  // Mesh peers
  const peersEl = document.getElementById('peers');
  const peers = state.peers || {};
  const pnames = Object.keys(peers);
  if (pnames.length === 0) {
    peersEl.innerHTML = '<div style="color:#666">no mesh peers discovered</div>';
  } else {
    peersEl.innerHTML = pnames.map(name => {
      const p = peers[name];
      return `<div class="peer">
        <span class="peer-name">${name}</span>
        <span class="stat"><label>bat </label><value>${p.battery || '?'}%</value></span>
        <span class="stat"><label>rssi </label><value>${p.rssi || '?'}</value></span>
        <span class="stat"><label>hops </label><value>${p.hops || '?'}</value></span>
        <span class="stat"><label>via </label><value>${p.seen_by || '?'}</value></span>
      </div>`;
    }).join('');
  }

  // Topology
  renderTopo(nodes, peers);
}

function renderTopo(nodes, peers) {
  const el = document.getElementById('topo');
  const ips = Object.keys(nodes);
  if (ips.length === 0) {
    el.innerHTML = '<span style="color:#666">waiting for nodes...</span>';
    return;
  }

  let html = '<div class="topo-node"><div class="topo-icon">[Pi]</div><div class="topo-label">bridge</div></div>';
  ips.forEach(ip => {
    const n = nodes[ip];
    html += ' <span class="topo-line">---</span> ';
    html += `<div class="topo-node"><div class="topo-icon">[${n.online ? '*' : 'x'}]</div><div class="topo-label">${n.name}</div></div>`;
  });

  const peerNames = Object.keys(peers);
  const nodeNames = ips.map(ip => nodes[ip].name);
  peerNames.forEach(name => {
    if (!nodeNames.includes(name)) {
      const p = peers[name];
      html += ' <span class="topo-line">~~~</span> ';
      html += `<div class="topo-node"><div class="topo-icon">[${p.hops || '?'}h]</div><div class="topo-label">${name}</div></div>`;
    }
  });

  el.innerHTML = html;
}

function formatUptime(s) {
  if (!s) return '?';
  if (s < 60) return s + 's';
  if (s < 3600) return Math.floor(s/60) + 'm';
  return Math.floor(s/3600) + 'h' + Math.floor((s%3600)/60) + 'm';
}

function sendCmd() {
  const nodeIp = document.getElementById('cmd-node').value;
  const cmd = document.getElementById('cmd-input').value;
  if (!nodeIp || !cmd) return;
  ws.send(JSON.stringify({type: 'cmd', node: nodeIp, cmd: cmd}));
  document.getElementById('cmd-input').value = '';
}

document.getElementById('cmd-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendCmd();
});

connect();
</script>
</body>
</html>"""


def main():
    bridge = MeshBridge()
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        RNS.log("Bridge shutting down", RNS.LOG_NOTICE)
        sys.exit(0)


if __name__ == "__main__":
    main()
