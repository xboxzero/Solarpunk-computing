# Solarpunk Computing

An open-source, solar-powered wearable computer built on ESP32-S3. Program it from Safari on your iPhone. Devices automatically discover each other and form encrypted off-grid mesh networks. Optionally connects to a Raspberry Pi 5 hub for local LLM AI agent capabilities.

**Firmware version: 0.3.0**

## What Is This?

A tiny, solar-powered computer you can wear that:
- **Hosts a web IDE** -- connect from Safari on your iPhone, no app needed
- **Forms mesh networks** -- devices auto-discover each other using ESP-NOW (no WiFi router needed)
- **Runs on sunlight** -- solar panel + LiPo battery with deep sleep for days of operation
- **Programmable** -- write and run scripts from the browser-based terminal
- **AI-powered** -- ask questions or run autonomous agent tasks via a local LLM on Pi 5
- **Encrypted** -- AES-256-GCM on all mesh traffic, auth tokens on API
- **Open source** -- hardware designs, firmware, everything

## Hardware

| Component | Part | Purpose | Cost |
|-----------|------|---------|------|
| MCU | ESP32-S3-WROOM-1 | Dual-core 240MHz, WiFi+BLE, 512KB SRAM, 8MB PSRAM | $3.50 |
| Solar Panel | 5V 1W (80x60mm) | Energy harvesting | $2.00 |
| Charge Controller | TP4056 + DW01A | LiPo charging with protection | $0.25 |
| Battery | 3.7V 1000mAh LiPo | ~8hr active, days in mesh-sleep mode | $3.00 |
| Voltage Reg | ME6211 3.3V LDO | Ultra-low quiescent current (40uA) | $0.10 |
| Display (optional) | SSD1306 0.96" OLED | Status display via I2C | $1.50 |
| Enclosure | 3D printed (STL files in hardware/) | Wrist-mount or clip-on | ~$2 |

**Total BOM: ~$15** (see `hardware/bom.csv` for full list)

### Power Budget

| Mode | Current | Duration on 1000mAh |
|------|---------|---------------------|
| Active (WiFi AP + Web IDE) | ~120mA | 8 hours |
| Mesh relay (ESP-NOW only) | ~20mA | 50 hours |
| Mesh sleep (wake every 30s) | ~0.5mA avg | 83 days |
| Deep sleep (RTC timer wake) | ~10uA | Years |

## Quick Start

### 1. Flash the firmware
```bash
# Install ESP-IDF v5.x (https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/)
cd Solarpunk-computing
idf.py set-target esp32s3   # or: idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

### 2. Connect from iPhone
- Join WiFi: `SolarpunkNode-XXXX` (XXXX = last 2 bytes of MAC, no password)
- Safari opens automatically (captive portal)
- You're in the web terminal -- start typing commands

### 3. Mesh networking
- Power on 2+ devices near each other
- They auto-discover within seconds via ESP-NOW
- Type `peers` to see discovered nodes
- Type `send hello` to broadcast, or `send @NodeName hello` for unicast

### 4. (Optional) Set up Pi 5 hub
- Run `pi-server/setup-llm.sh` on a Raspberry Pi 5 to install llama.cpp
- Set up WiFi hotspot "solarpunk-pi" on the Pi
- ESP32 auto-connects and gains LLM access (`ask` and `agent` commands)

## Architecture

```
iPhone Safari
  |
  | WiFi AP (captive portal)
  v
+------------------------------------------------------+
|  ESP32-S3 Node                                       |
|                                                      |
|  +----------+ +-----------+ +----------+ +---------+ |
|  | Web      | | Script    | | Power    | | LLM     | |
|  | Server   | | Engine    | | Manager  | | Client  | |
|  | HTTP+WS  | | Commands  | | Solar+   | | (Pi 5)  | |
|  |          | | + SPIFFS  | | Sleep    | |         | |
|  +----------+ +-----------+ +----------+ +---------+ |
|  +----------+ +--------------------------------------+|
|  | Security | | Mesh Network (ESP-NOW)               ||
|  | AES-256  | | Auto-discovery, multi-hop, encrypted ||
|  | GCM      | +--------------------------------------+|
|  +----------+                                        |
+------------------------------------------------------+
       ^  ESP-NOW (250m, no router)        ^ WiFi STA
       |                                   |
+------------------+        +--------------------------+
| Other Solarpunk  |        | Raspberry Pi 5 Hub       |
| Nodes            |        | - llama.cpp LLM server   |
| (auto-discovered)|        | - Web terminal (:8822)   |
+------------------+        | - Mesh bridge  (:8833)   |
                            | - Reticulum P2P terminal |
                            | - Agent orchestrator     |
                            +--------------------------+
```

## Project Structure

```
main/                         # ESP-IDF firmware source
  main.cpp                    # Entry point, WiFi AP+STA, task startup
  config.h                    # All configuration in one place
  web/
    webserver.cpp/h           # HTTP server + WebSocket terminal
    captive.cpp/h             # Captive portal (auto-open on iPhone)
    static/
      index.html              # Web terminal UI
      style.css               # Mobile-first dark theme
      app.js                  # WebSocket client, command history
  mesh/
    mesh.cpp/h                # ESP-NOW mesh networking + multi-hop routing
    discovery.cpp/h           # Auto-discovery + peer table
    protocol.h                # Message types, formats, beacon structure
  power/
    solar.cpp/h               # Battery + solar monitoring (ADC)
    sleep.cpp/h               # Deep sleep, mesh-sleep, idle detection
  scripting/
    engine.cpp/h              # Command interpreter (all terminal commands)
  llm/
    llm_client.cpp/h          # LLM query + autonomous agent mode
  security/
    crypto.cpp/h              # AES-256-GCM encrypt/decrypt, auth tokens
  hal/
    uart.cpp/h                # Serial I/O
    gpio.cpp/h                # Pin control, LED, charge status
hub/                          # Pi 5 backend services
  terminal_server.py          # Reticulum E2E encrypted P2P shell
  terminal_client.py          # CLI client for Reticulum terminal
  web_terminal.py             # Browser terminal (xterm.js, port 8822)
  mesh_bridge.py              # ESP32 mesh <-> Reticulum bridge (port 8833)
  bridge_client.py            # CLI client to query mesh bridge
  connect.sh                  # Quick-connect helper
  agent-orchestrator/         # Rust multi-agent TUI/web dashboard
pi-server/
  setup-llm.sh               # One-command LLM install on Pi 5
hardware/
  bom.csv                     # Bill of materials with prices
  schematic/                  # KiCad PCB files
  enclosure/                  # 3D printable STL files
CMakeLists.txt                # ESP-IDF build system
partitions.csv                # Flash partition layout (1.92MB app + 64KB SPIFFS)
sdkconfig.defaults            # ESP-IDF defaults (WiFi, ESP-NOW, SPIFFS, power save)
LICENSE                       # MIT
```

## Web Terminal Commands

| Command | Description |
|---------|-------------|
| `help` | List all commands |
| `status` | Node name, battery %, solar mV, peers, uptime, LLM status |
| `version` | Firmware version |
| `free` | Free heap memory |
| `uptime` | Time since boot |
| `peers` | List discovered mesh nodes |
| `send <msg>` | Broadcast message to all nodes |
| `send @<node> <msg>` | Send to specific node |
| `exec @<node> <cmd>` | Run command on remote node |
| `gpio <pin> <0\|1>` | Set GPIO pin |
| `read <pin>` | Read digital GPIO pin |
| `adc <pin>` | Read analog value |
| `battery` | Battery voltage and percentage |
| `solar` | Solar panel voltage |
| `sleep <sec>` | Enter deep sleep |
| `ls` | List saved scripts |
| `cat <file>` | Read a script |
| `write <file> <content>` | Save a script to SPIFFS |
| `rm <file>` | Delete a script |
| `ask <question>` | Ask the LLM (requires Pi connection) |
| `agent <task>` | Autonomous AI agent (LLM executes commands) |
| `token` | Show/set auth token |
| `reboot` | Reboot the node |

## Mesh Protocol

Devices use ESP-NOW (peer-to-peer, no router, 250m range):

- **Discovery**: Beacon broadcast every 10s with node ID, battery %, solar status, peer count, capabilities, route advertisements
- **Routing**: Automatic multi-hop (up to 6 hops), each node maintains a neighbor table with signal strength and hop count
- **Encryption**: AES-256-GCM on all payloads (12-byte IV + ciphertext + 16-byte auth tag)
- **Message types**: BEACON, TEXT, FILE, SCRIPT, SENSOR, ACK, PING, SLEEP_SYNC, EXEC, RESULT, ROUTE
- **Max payload**: 250 bytes per ESP-NOW frame
- **Sleep sync**: Nodes agree on wake windows (30s sleep, 50ms listen) to save power
- **Peer expiry**: Nodes removed from table after 90s without beacon

## Pi 5 Hub Services

The Pi 5 acts as an optional hub, running services that extend the mesh network:

| Service | Port | Purpose |
|---------|------|---------|
| Web terminal | 8822 | Browser-based terminal (xterm.js + WebSocket), can run Claude Code |
| Mesh bridge | 8833 | ESP32 mesh <-> Reticulum bridge with live web dashboard |
| Reticulum terminal | 4242 | E2E encrypted P2P shell over Reticulum transport |
| LLM server | 8080 | llama.cpp HTTP API (TinyLlama 1.1B Q4_K_M) |
| Agent orchestrator | 8888 | Multi-agent TUI/web dashboard (Rust) |

### Pi WiFi Hotspot
- SSID: `solarpunk-pi` / Password: `solarpunk`
- Interface: `ap0` (concurrent AP+STA on Pi 5)
- IP: `10.42.0.1/24`, DHCP range: `10.42.0.10-254`
- ESP32 auto-connects via STA mode

### How the Mesh Bridge Works
1. Pi runs WiFi hotspot on `ap0`
2. ESP32 connects via STA mode to `solarpunk-pi` network
3. `mesh_bridge.py` polls ESP32's HTTP API (`/api/status`, `/api/mesh/peers`) every 5s
4. Exposes mesh state as Reticulum destination (`solarpunk.mesh`)
5. Web dashboard at `:8833` shows live topology, node stats, remote command exec
6. Any Reticulum peer can query mesh state via `bridge_client.py`

## Low Power Design

The firmware aggressively manages power:
1. **Adaptive WiFi**: AP disables after 5 minutes with no connected clients
2. **Mesh duty cycle**: ESP-NOW wake every 30s, listen for 50ms, sleep rest
3. **Solar tracking**: ADC monitors panel voltage, detects charging state
4. **Task shedding**: Non-essential tasks disabled below 20% battery, critical mode at 10%
5. **Deep sleep**: Full shutdown with RTC wake after 10 minutes idle

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web IDE (terminal UI) |
| `/api/status` | GET | JSON: node name, battery, solar, peers, uptime, LLM |
| `/api/run` | POST | Execute a command (auth token required) |
| `/ws` | WebSocket | Real-time terminal I/O |

Auth token: set `SP_AUTH_TOKEN` in `config.h` (default: `solarpunk2026`).

## License

MIT License -- build whatever you want.

## Contributing

PRs welcome. Open an issue first for big changes.
