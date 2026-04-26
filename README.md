# Solarpunk Computing

A solar-powered mesh computing platform. ESP32 nodes form encrypted off-grid mesh networks and connect to a Raspberry Pi 5 hub running a browser-accessible web terminal, local AI, and mesh management.

## How It Works

```
  Phone/Laptop                     Phone/Laptop
       |                                |
       | WiFi (captive portal)          | WiFi / Tailscale
       v                                v
+--------------------+      +----------------------------+
| ESP32 Node         |      | Raspberry Pi 5 Hub         |
|                    | WiFi |                            |
| Web terminal       |----->| sp-hub (Rust)              |
| Mesh networking    |      |   Web terminal  :8822      |
| Solar + battery    |      |   Mesh bridge   :8833      |
| Script engine      |      |                            |
| LLM client         |      | LLM server      :8080     |
| AES-256 encryption |      |   llama.cpp (TinyLlama)   |
+--------------------+      |                            |
       ^                    | Agent orchestrator :8888   |
       | ESP-NOW (250m)     |   Multi-agent TUI + web   |
       v                    +----------------------------+
+--------------------+
| Other ESP32 Nodes  |
| (auto-discovered)  |
+--------------------+
```

## Pi 5 Web Terminal System

The Pi 5 hub is the central piece -- open a browser on any device and get a full shell on the Pi. The web terminal runs heavy workloads like Claude Code with no issues.

**sp-hub** is a single Rust binary that replaces the older Python scripts. It serves two main things:

- **Web terminal** (port 8822) -- xterm.js frontend over WebSocket, spawns real PTY shell sessions with process group isolation, zombie reaping, session timeout, and up to 4 concurrent sessions. Handles fast output (16KB read buffer) and proper cleanup on disconnect.
- **Mesh bridge** (port 8833) -- polls ESP32 nodes on the 10.42.0.x subnet via HTTP every 5s, builds a live topology map, and exposes remote command execution through a web dashboard.

### Running sp-hub

```bash
cd ~/Solarpunk-computing/hub/sp-hub
cargo build --release
./target/release/sp-hub
```

Then open `http://<pi-ip>:8822` from any browser. On a phone, it works full-screen.

### sp CLI

Command-line tool for interacting with the hub:

```bash
cd ~/Solarpunk-computing/hub/sp-cli
cargo build --release

sp connect              # interactive terminal via WebSocket
sp mesh status          # mesh network topology
sp mesh send <ip> <cmd> # send command to a node through the bridge
sp status               # query ESP32 node directly
sp flash                # build and flash firmware via idf.py
```

### Agent Orchestrator

Multi-agent AI dashboard with both a terminal UI (ratatui) and web interface:

```bash
cd ~/Solarpunk-computing/hub/agent-orchestrator
cargo build --release
./target/release/agent-orchestrator
```

Web UI at `http://<pi-ip>:8888`. Supports Claude (auto-detects OAuth token from Claude Code), OpenAI, and local llama.cpp backends. Agent roles: General, Coder, Researcher, SysAdmin, MeshOperator.

### LLM Server

```bash
cd ~/Solarpunk-computing/pi-server
./setup-llm.sh
```

Builds llama.cpp on the Pi, downloads TinyLlama 1.1B (~670MB), and sets up a systemd service on port 8080. ESP32 nodes use the `ask` and `agent` commands to query it.

### WiFi Hotspot

The Pi runs a WiFi hotspot so ESP32 nodes can connect:

```bash
sudo nmcli device wifi hotspot ifname wlan0 con-name solarpunk-pi ssid solarpunk-pi password solarpunk
```

Network: `10.42.0.1/24`, DHCP `10.42.0.10-254`. ESP32 nodes auto-connect when `SP_STA_ENABLED=1` in `main/config.h`.

## ESP32 Nodes

Each node is a self-contained solar-powered computer (~$12 BOM):

- **WiFi AP** -- phone connects directly, Safari opens a web terminal via captive portal
- **ESP-NOW mesh** -- auto-discovery, multi-hop routing (up to 6 hops, 250m per hop), no router needed
- **AES-256-GCM** -- all mesh traffic encrypted
- **Solar + battery** -- LiPo charging, deep sleep modes, days of mesh operation
- **Script engine** -- save and run scripts from SPIFFS
- **LLM client** -- queries the Pi hub for AI when connected

### Quick Start (ESP32)

```bash
source ~/esp/esp-idf/export.sh
cd ~/Solarpunk-computing
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

Join WiFi `SolarpunkNode-XXXX` from your phone -- Safari auto-opens the terminal.

### ESP32 Terminal Commands

| Command | Description |
|---------|-------------|
| `status` | Battery %, solar mV, peers, uptime, LLM status |
| `peers` | List discovered mesh nodes |
| `send <msg>` | Broadcast to all nodes |
| `send @<node> <msg>` | Unicast to specific node |
| `exec @<node> <cmd>` | Run command on remote node |
| `gpio`, `adc`, `battery`, `solar` | Hardware I/O |
| `ask <question>` | Query LLM (requires Pi connection) |
| `agent <task>` | Autonomous AI agent |
| `ls`, `cat`, `write`, `rm` | Script file management |
| `sleep <sec>` | Enter deep sleep |

## Hardware

### ESP32 Node BOM

| Component | Part | Cost |
|-----------|------|------|
| MCU | ESP32-S3-WROOM-1 (8MB flash, 8MB PSRAM) | $3.50 |
| Solar Panel | 5V 1W (80x60mm) | $2.00 |
| Charge Controller | TP4056 + DW01A | $0.25 |
| Battery | 3.7V 1000mAh LiPo | $3.00 |
| Voltage Regulator | ME6211 3.3V LDO (40uA quiescent) | $0.10 |
| Display (optional) | SSD1306 0.96" OLED | $1.50 |

### Solarpunk Pi v3 Board

Custom PCB design in `hardware/solarpunk-pi-v3/` (KiCad 9). Multi-processor architecture:

- **RK3576** -- main compute (Linux)
- **RP2350** -- radio co-processor
- **RK3506J** -- industrial I/O

Datasheet and BOM in `hardware/`.

## Project Structure

```
main/                       ESP32 firmware (ESP-IDF C++)
  main.cpp                  Entry point -- WiFi AP+STA, task startup
  config.h                  All configuration
  web/                      HTTP server + WebSocket terminal + captive portal
  mesh/                     ESP-NOW mesh networking + multi-hop routing
  power/                    Battery/solar monitoring + deep sleep
  scripting/                Command interpreter
  llm/                      LLM query + autonomous agent
  security/                 AES-256-GCM encryption
  hal/                      GPIO, UART
hub/                        Pi 5 services
  sp-hub/                   Rust: web terminal + mesh bridge (primary)
  sp-cli/                   Rust: CLI tool (connect, mesh, flash, status)
  agent-orchestrator/       Rust: multi-agent TUI + web dashboard
  web_terminal.py           Python web terminal (legacy)
  mesh_bridge.py            Python mesh bridge (legacy)
pi-server/
  setup-llm.sh              One-command LLM install on Pi 5
hardware/
  solarpunk-pi-v3/          KiCad PCB design (v3 custom board)
  bom_v3.csv                Bill of materials
CMakeLists.txt              ESP-IDF build
partitions.csv              Flash partition layout
sdkconfig.defaults          ESP-IDF defaults
```

## Setup Guide

See [HOWTO.md](HOWTO.md) for detailed installation instructions.

## License

MIT
