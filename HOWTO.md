# How To Guide

Step-by-step instructions for building, flashing, using, and extending the Solarpunk Wearable Computer.

---

## 1. Prerequisites

### Hardware
- **ESP32-S3-WROOM-1** (8MB flash, 8MB PSRAM) -- or standard ESP32
- **USB-C cable** for flashing
- See `hardware/bom.csv` for the full parts list (~$15 total)

### Software
- **ESP-IDF v5.x** -- Espressif's official framework
- **Git**
- **Python 3.8+** (included with ESP-IDF install)

### Optional
- **Raspberry Pi 5** -- for LLM server, mesh bridge, web terminal
- **Reticulum** (`pip install rns`) -- for encrypted P2P terminal

---

## 2. Install ESP-IDF

Follow the official guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/

Quick version (Linux/macOS):
```bash
mkdir -p ~/esp && cd ~/esp
git clone -b v5.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
source export.sh
```

Verify:
```bash
idf.py --version
```

> You must run `source ~/esp/esp-idf/export.sh` in every new terminal session before building.

---

## 3. Clone and Build

```bash
git clone https://github.com/xboxzero/Solarpunk-computing.git
cd Solarpunk-computing

# Set target (pick one)
idf.py set-target esp32s3   # for ESP32-S3
idf.py set-target esp32     # for original ESP32

# Build
idf.py build
```

Build output goes to `build/`. The firmware binary is `build/solarpunk-wearable.bin`.

### Configuration

All settings are in `main/config.h`. Key things you may want to change:

| Setting | Default | Purpose |
|---------|---------|---------|
| `SP_AUTH_TOKEN` | `"solarpunk2026"` | API authentication token |
| `SP_MESH_KEY` | `"SolarpunkMeshKey!..."` | AES-256 encryption key (32 bytes) |
| `SP_STA_SSID` | `"solarpunk-pi"` | Pi WiFi network to connect to |
| `SP_STA_PASS` | `"solarpunk"` | Pi WiFi password |
| `SP_STA_ENABLED` | `1` | Set to 0 if no Pi hub |
| `SP_LLM_HOST` | `"10.42.0.1"` | Pi's IP on hotspot network |
| `SP_DISPLAY_ENABLED` | `0` | Set to 1 if OLED connected |

### Partition Layout

The flash is divided (see `partitions.csv`):
- **nvs**: 24KB -- WiFi credentials, calibration
- **phy_init**: 4KB -- RF calibration
- **factory**: 1.92MB -- firmware application
- **scripts**: 64KB -- SPIFFS for user scripts

---

## 4. Flashing

Connect the ESP32 via USB and flash:
```bash
idf.py -p /dev/ttyUSB0 flash monitor
```

The `monitor` flag opens a serial console so you can see boot logs. Press `Ctrl+]` to exit the monitor.

If the port is different, check:
```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

### Troubleshooting Flash

- **Permission denied**: `sudo usermod -a -G dialout $USER` then log out and back in
- **Port busy**: Make sure no other serial monitor is open
- **Boot loop**: Run `idf.py erase-flash` then re-flash

---

## 5. Connecting from iPhone

1. Open **Settings > WiFi** on your iPhone
2. Join the network `SolarpunkNode-XXXX` (XXXX = last 2 bytes of the device MAC address, no password)
3. Safari opens automatically via captive portal
4. You're now in the web terminal

If Safari doesn't auto-open, navigate to `http://192.168.4.1` manually.

### Web Terminal

The terminal is a command-line interface in your browser. Type commands and press Enter.

Use arrow keys for command history. The connection is via WebSocket for real-time I/O.

### First Commands to Try

```
help              # see all available commands
status            # battery, solar, peers, uptime
peers             # list mesh neighbors
battery           # battery voltage and percentage
solar             # solar panel voltage
version           # firmware version
free              # available heap memory
```

---

## 6. Terminal Commands Reference

### System
| Command | Description |
|---------|-------------|
| `help` | List all commands |
| `status` | Full system status (battery, solar, peers, uptime, LLM) |
| `version` | Firmware version |
| `whoami` | Device name |
| `free` | Free heap memory |
| `uptime` | Time since boot |
| `reboot` | Reboot the device |

### GPIO / Hardware
| Command | Description |
|---------|-------------|
| `gpio <pin> <0\|1>` | Set a GPIO pin high or low |
| `read <pin>` | Read a digital GPIO pin |
| `adc <pin>` | Read analog value from ADC pin |
| `battery` | Battery voltage (mV) and percentage |
| `solar` | Solar panel voltage (mV) |

### Mesh Networking
| Command | Description |
|---------|-------------|
| `peers` | List all discovered mesh nodes |
| `send <message>` | Broadcast to all mesh nodes |
| `send @<name> <message>` | Send to a specific node by name |
| `exec @<name> <command>` | Execute a command on a remote node |

### File Management (SPIFFS)
| Command | Description |
|---------|-------------|
| `ls` | List saved scripts |
| `cat <filename>` | Read a file |
| `write <filename> <content>` | Save a file |
| `rm <filename>` | Delete a file |

### AI (requires Pi 5 connection)
| Command | Description |
|---------|-------------|
| `ask <question>` | Ask the local LLM a question |
| `agent <task>` | Autonomous agent: LLM plans and executes commands |

### Security
| Command | Description |
|---------|-------------|
| `token` | Show current auth token |
| `encrypt-status` | Show mesh encryption status |

### Power
| Command | Description |
|---------|-------------|
| `sleep <seconds>` | Enter deep sleep for N seconds |

---

## 7. Mesh Networking

### How It Works

Devices communicate using ESP-NOW, a peer-to-peer protocol that works without a WiFi router. Range is approximately 250 meters line-of-sight.

1. Each node broadcasts a **beacon** every 10 seconds containing: node name, battery %, solar status, peer count, capabilities, and route advertisements
2. Nodes that hear beacons add the sender to their **peer table** (max 16 peers)
3. Messages can be **relayed** through intermediate nodes (up to 6 hops)
4. All payloads are encrypted with **AES-256-GCM**
5. Peers are expired after **90 seconds** without a beacon

### Message Types

| Type | Purpose |
|------|---------|
| BEACON | Periodic node announcement |
| TEXT | Chat messages |
| FILE | File transfer |
| SCRIPT | Script deployment to remote node |
| SENSOR | Sensor data sharing |
| EXEC | Remote command execution |
| RESULT | Response to EXEC |
| PING / ACK | Connectivity check |
| SLEEP_SYNC | Coordinate sleep windows |
| ROUTE | Routing table updates |

### Testing Mesh

With 2+ nodes powered on:
```
peers                          # should show other nodes
send hello everyone            # broadcast
send @OtherNode ping           # unicast
exec @OtherNode status         # run command on remote node
```

---

## 8. Power Management

### Modes

The firmware automatically transitions between power modes:

1. **Active** (~120mA) -- WiFi AP running, web IDE available, mesh active
2. **Mesh relay** (~20mA) -- WiFi AP disabled (no clients for 5 min), mesh stays active
3. **Mesh sleep** (~0.5mA avg) -- Node wakes every 30s, listens for 50ms, sleeps rest
4. **Deep sleep** (~10uA) -- Full shutdown, RTC timer wakes after configured duration

### Automatic Transitions

- **Active -> Mesh relay**: No WiFi clients connected for 5 minutes (`SP_WIFI_AP_INACTIVE_MS`)
- **Active -> Deep sleep**: No activity for 10 minutes (`SP_IDLE_SLEEP_MS`)
- **Battery < 20%**: Non-essential tasks disabled
- **Battery < 10%**: Critical mode -- only mesh relay, no WiFi AP

### Solar Charging

The TP4056 charge controller handles LiPo charging from the solar panel automatically. The firmware monitors:
- Battery voltage via ADC (pin 4, voltage divider, range 3200-4200mV)
- Solar panel voltage via ADC (pin 5)
- Charge status pin (GPIO 15, from TP4056 CHRG output)

---

## 9. Pi 5 Hub Setup (Optional)

The Raspberry Pi 5 extends the network with LLM capabilities, a web terminal, and a mesh bridge.

### LLM Server

Install llama.cpp and a small model:
```bash
cd Solarpunk-computing/pi-server
chmod +x setup-llm.sh
./setup-llm.sh
```

This builds llama.cpp, downloads TinyLlama 1.1B (Q4_K_M, ~670MB), creates a systemd service, and starts the HTTP server on port 8080.

Verify:
```bash
curl http://localhost:8080/health
```

### WiFi Hotspot

Set up a WiFi hotspot so ESP32 nodes can connect:
```bash
# Using NetworkManager
nmcli device wifi hotspot ifname wlan0 con-name solarpunk-pi ssid solarpunk-pi password solarpunk

# For concurrent AP+STA (internet + hotspot), configure an ap0 virtual interface:
# Interface: ap0, IP: 10.42.0.1/24, DHCP: 10.42.0.10-254
# Note: Pi 5 requires AP and STA on the same WiFi channel
```

ESP32 nodes will auto-connect to `solarpunk-pi` if `SP_STA_ENABLED` is set in `config.h`.

### Hub Services

All services run as systemd user services:

```bash
# Install dependencies
pip install rns aiohttp websockets

# Terminal server (Reticulum P2P shell, port 4242)
cd hub
python terminal_server.py

# Web terminal (browser-based, port 8822)
python web_terminal.py

# Mesh bridge (ESP32 mesh <-> Reticulum, port 8833)
python mesh_bridge.py
```

#### Service Descriptions

**Web Terminal** (`web_terminal.py`, port 8822)
- Browser-based terminal using xterm.js
- Supports heavy processes like Claude Code
- Process group isolation, zombie cleanup
- Max 4 concurrent sessions

**Mesh Bridge** (`mesh_bridge.py`, port 8833)
- Polls ESP32 nodes on the `10.42.0.x` subnet via HTTP API
- Web dashboard shows live mesh topology, node stats
- Remote command execution from the dashboard
- Bridges mesh state into Reticulum network

**Reticulum Terminal** (`terminal_server.py`, port 4242)
- End-to-end encrypted shell access
- Works over any Reticulum transport (TCP, UDP, LoRa, serial)
- Connect with: `python terminal_client.py`

**Agent Orchestrator** (`hub/agent-orchestrator/`)
- Rust-based multi-agent TUI and web dashboard (port 8888)
- Supports Claude, OpenAI, and local llama.cpp backends
- Agent roles: General, Coder, Researcher, SysAdmin, MeshOperator
- Build with: `cd hub/agent-orchestrator && cargo build --release`

### Access URLs

From a device on the same network as the Pi:
- Web terminal: `http://<pi-ip>:8822`
- Mesh dashboard: `http://<pi-ip>:8833`
- LLM health: `http://<pi-ip>:8080/health`
- Agent orchestrator: `http://<pi-ip>:8888`

---

## 10. API Reference

The ESP32 node exposes an HTTP API for programmatic access.

### GET /api/status
Returns JSON:
```json
{
  "node": "SolarpunkNode-D409",
  "battery_pct": 72,
  "battery_mv": 3890,
  "solar_mv": 4100,
  "charging": true,
  "peers": 2,
  "uptime_s": 3600,
  "llm_connected": true,
  "firmware": "0.3.0"
}
```

### POST /api/run
Execute a command. Requires auth token.
```bash
curl -X POST http://192.168.4.1/api/run \
  -H "Authorization: Bearer solarpunk2026" \
  -d "status"
```

### WebSocket /ws
Real-time terminal. Send text commands, receive output.

---

## 11. Security

### Mesh Encryption
- All ESP-NOW payloads encrypted with AES-256-GCM
- 32-byte key configured in `config.h` (`SP_MESH_KEY`)
- Each message has a unique 12-byte IV and 16-byte authentication tag
- Change the default key before deploying!

### API Authentication
- `SP_AUTH_TOKEN` required for `/api/run` endpoint
- Default: `solarpunk2026` -- change this in `config.h`
- Web terminal on WebSocket uses the same token (stored in browser localStorage)

### What to Change Before Deploying
1. `SP_AUTH_TOKEN` -- unique per deployment
2. `SP_MESH_KEY` -- unique per mesh network (32 bytes)
3. `SP_MESH_PMK` -- ESP-NOW primary master key (16 chars)

---

## 12. Hardware Assembly

### Wiring

```
Solar Panel (5V) --> TP4056 IN+/IN-
TP4056 BAT+/BAT- --> LiPo Battery
TP4056 OUT+/OUT- --> ME6211 IN/GND
ME6211 OUT/GND --> ESP32 3V3/GND

Voltage divider (battery monitoring):
BAT+ --> 100K --> ADC pin 4 --> 100K --> GND

Voltage divider (solar monitoring):
Solar+ --> 100K --> ADC pin 5 --> 100K --> GND

TP4056 CHRG --> GPIO 15 (charge status, active low)

Optional OLED:
SDA --> GPIO 21
SCL --> GPIO 22
```

### Pin Reference

| GPIO | Function |
|------|----------|
| 2 | Onboard LED |
| 4 | Battery ADC (voltage divider) |
| 5 | Solar ADC (voltage divider) |
| 15 | TP4056 charge status |
| 21 | I2C SDA (optional OLED) |
| 22 | I2C SCL (optional OLED) |

---

## 13. Troubleshooting

### ESP32 won't flash
- Check USB cable (must be data-capable, not charge-only)
- Hold BOOT button while pressing RESET, then release BOOT
- Try `idf.py erase-flash` then re-flash

### Can't connect from iPhone
- Make sure you're joining `SolarpunkNode-XXXX`, not your home WiFi
- If captive portal doesn't appear, open Safari and go to `http://192.168.4.1`
- Check serial monitor for WiFi AP status

### Mesh nodes don't see each other
- Nodes must use the same `SP_MESH_KEY` and `SP_MESH_CHANNEL`
- Check `peers` command -- discovery takes up to 10s (one beacon interval)
- Reduce distance for testing (ESP-NOW range varies with environment)

### LLM commands fail ("ask", "agent")
- ESP32 must be connected to Pi's hotspot (check `status` for LLM connection)
- Verify llama.cpp is running: `curl http://10.42.0.1:8080/health`
- Check `SP_LLM_HOST` and `SP_LLM_PORT` in `config.h`

### Battery reads 0% or wrong values
- Check voltage divider wiring on ADC pins 4 and 5
- Verify `SP_BATTERY_ADC_PIN` and `SP_SOLAR_ADC_PIN` in `config.h`

---

## License

MIT
