# Installation & Setup

## 1. Pi 5 Hub Setup

### Install the LLM Server

```bash
cd ~/Solarpunk-computing/pi-server
chmod +x setup-llm.sh
./setup-llm.sh
```

This builds llama.cpp, downloads TinyLlama 1.1B (~670MB), and creates a systemd service. The server runs on port 8080.

To run as a service:
```bash
mkdir -p ~/.config/systemd/user
cp ~/solarpunk-llm/solarpunk-llm.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now solarpunk-llm
```

Verify: `curl http://localhost:8080/health`

### Set Up WiFi Hotspot

ESP32 nodes connect to the Pi over WiFi. Create a hotspot:

```bash
sudo nmcli device wifi hotspot ifname wlan0 con-name solarpunk-pi ssid solarpunk-pi password solarpunk
```

This creates network `solarpunk-pi` on `10.42.0.1/24`. ESP32 nodes auto-connect if `SP_STA_ENABLED=1` in `main/config.h`.

### Build and Run sp-hub

sp-hub is the Rust replacement for the Python hub scripts. It provides the web terminal and mesh bridge:

```bash
cd ~/Solarpunk-computing/hub/sp-hub
cargo build --release
./target/release/sp-hub
```

Services:
- **Web terminal** at `http://<pi-ip>:8822` -- browser shell (xterm.js), handles heavy processes like Claude Code
- **Mesh bridge** at `http://<pi-ip>:8833` -- live mesh topology, node stats, remote command exec

### Build sp CLI (Optional)

```bash
cd ~/Solarpunk-computing/hub/sp-cli
cargo build --release
cp target/release/sp ~/.local/bin/
```

Usage:
```bash
sp connect              # interactive terminal via WebSocket
sp mesh peers           # list mesh nodes
sp mesh send "hello"    # broadcast to mesh
sp status               # hub status
```

### Agent Orchestrator (Optional)

Multi-agent AI dashboard with TUI and web UI:

```bash
cd ~/Solarpunk-computing/hub/agent-orchestrator
cargo build --release
./target/release/agent-orchestrator
```

Web UI at `http://<pi-ip>:8888`. Supports Claude, OpenAI, and local llama.cpp backends.

---

## 2. ESP32 Firmware

### Prerequisites

- ESP32-S3 or ESP32 dev board + USB-C cable
- ESP-IDF v5.x installed ([official guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/))

Quick ESP-IDF install:
```bash
mkdir -p ~/esp && cd ~/esp
git clone -b v5.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf && ./install.sh esp32s3
source export.sh
```

### Configure

Edit `main/config.h` before building:

| Setting | Default | Change if... |
|---------|---------|-------------|
| `SP_AUTH_TOKEN` | `solarpunk2026` | Always change for deployment |
| `SP_MESH_KEY` | `SolarpunkMeshKey!...` | Always change (32-byte AES key) |
| `SP_STA_SSID` | `solarpunk-pi` | Your Pi hotspot has a different name |
| `SP_STA_PASS` | `solarpunk` | Your Pi hotspot has a different password |
| `SP_STA_ENABLED` | `1` | Set to `0` if no Pi hub |
| `SP_LLM_HOST` | `10.42.0.1` | Pi has a different IP |

### Build and Flash

```bash
cd ~/Solarpunk-computing
source ~/esp/esp-idf/export.sh

idf.py set-target esp32s3    # or: idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

Press `Ctrl+]` to exit the serial monitor.

### Connect from Phone

1. Join WiFi `SolarpunkNode-XXXX` (no password)
2. Safari opens automatically (captive portal)
3. You're in the web terminal

If Safari doesn't auto-open, go to `http://192.168.4.1`.

### Terminal Commands

**System**: `help`, `status`, `version`, `free`, `uptime`, `reboot`

**Mesh**: `peers`, `send <msg>`, `send @<node> <msg>`, `exec @<node> <cmd>`

**Hardware**: `gpio <pin> <0|1>`, `read <pin>`, `adc <pin>`, `battery`, `solar`

**Files**: `ls`, `cat <file>`, `write <file> <content>`, `rm <file>`

**AI** (requires Pi): `ask <question>`, `agent <task>`

**Power**: `sleep <seconds>`

---

## 3. How the System Works

### Boot Sequence (ESP32)

1. NVS and event loop initialize
2. Solar/battery ADC readings taken -- critical battery (<10%) triggers deep sleep
3. If waking from mesh-sleep timer, does a quick 50ms listen then sleeps again
4. Full boot: crypto init, WiFi AP+STA start, captive portal, web server, mesh, script engine, LLM client
5. Main loop monitors battery and idle timeout (deep sleep after 10min inactive)

### Mesh Networking

Nodes use ESP-NOW (peer-to-peer, no router, 250m range):

- **Discovery**: each node broadcasts a beacon every 10s with node ID, battery %, peer count, route ads
- **Routing**: automatic multi-hop (up to 6 hops), each node tracks neighbors by signal strength and hop count
- **Encryption**: AES-256-GCM on all payloads (12-byte IV + ciphertext + 16-byte auth tag)
- **Peer expiry**: nodes removed after 90s without beacon
- **Sleep sync**: nodes coordinate wake windows (30s sleep, 50ms listen)

Message types: BEACON, TEXT, FILE, SCRIPT, SENSOR, EXEC, RESULT, PING, ACK, SLEEP_SYNC, ROUTE

### Power Management

| Mode | Current | Battery life (1000mAh) |
|------|---------|----------------------|
| Active (WiFi AP + web terminal) | ~120mA | 8 hours |
| Mesh relay (AP off, ESP-NOW only) | ~20mA | 50 hours |
| Mesh sleep (wake 50ms every 30s) | ~0.5mA | 83 days |
| Deep sleep (RTC timer) | ~10uA | Years |

Transitions:
- AP disables after 5min with no connected clients
- Deep sleep after 10min idle
- Below 20% battery: non-essential tasks disabled
- Below 10%: critical mode, only mesh relay

### Pi Hub Architecture

The Pi runs three main services:

**sp-hub** -- single Rust binary replacing the Python scripts:
- Web terminal (port 8822): xterm.js + WebSocket, spawns PTY shell sessions, process group isolation, max 4 concurrent sessions
- Mesh bridge (port 8833): polls ESP32 nodes on 10.42.0.x subnet via HTTP API every 5s, builds live topology, exposes remote command execution

**LLM server** -- llama.cpp serving TinyLlama 1.1B (Q4_K_M) on port 8080. ESP32 nodes send questions via HTTP POST. The `agent` command lets the LLM plan and execute commands autonomously (up to 5 iterations).

**Agent orchestrator** -- Rust TUI + web dashboard (port 8888) for multi-agent workflows. Agent roles: General, Coder, Researcher, SysAdmin, MeshOperator. Auto-detects Claude OAuth token from Claude Code credentials.

### Network Topology

```
Internet
  |
  | wlan0 (STA)
  v
+--Pi 5-------------------------------+
| wlan0: internet uplink              |
| ap0: 10.42.0.1/24 (solarpunk-pi)   |
|   DHCP: 10.42.0.10-254             |
|                                     |
| sp-hub          :8822, :8833        |
| llama-server    :8080               |
| agent-orch      :8888               |
+--+----------------------------------+
   | ap0 (WiFi hotspot)
   |
   +--- ESP32 Node A (10.42.0.x)
   |      AP: SolarpunkNode-XXXX
   |      Mesh: ESP-NOW <-> other nodes
   |
   +--- ESP32 Node B (10.42.0.y)
          AP: SolarpunkNode-YYYY
          Mesh: ESP-NOW <-> other nodes
```

ESP32 nodes run AP+STA concurrently: the AP serves the phone web terminal, the STA connects to Pi's hotspot for LLM and management.

---

## 4. Troubleshooting

- **Flash fails**: use a data-capable USB cable, hold BOOT while pressing RESET, try `idf.py erase-flash`
- **No captive portal on iPhone**: go to `http://192.168.4.1` manually
- **Mesh nodes don't see each other**: must share `SP_MESH_KEY` and `SP_MESH_CHANNEL`, wait 10s for beacon
- **LLM commands fail**: check `status` for Pi connection, verify `curl http://10.42.0.1:8080/health`
- **Permission denied on serial port**: `sudo usermod -a -G dialout $USER`, then log out/in
