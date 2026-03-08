# Solarpunk Wearable Computer

An open-source, solar-powered wearable computer built on ESP32-S3. Program it from Safari on your iPhone. Devices automatically discover each other and form off-grid mesh networks.

## What Is This?

A tiny, solar-powered computer you can wear that:
- **Hosts a web IDE** -- connect from Safari on your iPhone, no app needed
- **Forms mesh networks** -- devices auto-discover each other using ESP-NOW (no WiFi router needed)
- **Runs on sunlight** -- solar panel + LiPo battery with deep sleep for days of operation
- **Programmable** -- write and deploy scripts from the browser-based editor
- **Open source** -- hardware designs, firmware, everything

## Hardware

| Component | Part | Purpose |
|-----------|------|---------|
| MCU | ESP32-S3-WROOM-1 | Dual-core 240MHz, WiFi+BLE, 512KB SRAM, 8MB PSRAM |
| Solar Panel | 5V 1W (80x60mm) | Energy harvesting |
| Charge Controller | TP4056 + DW01A | LiPo charging with protection |
| Battery | 3.7V 1000mAh LiPo | ~18hr active, days in mesh-sleep mode |
| Voltage Reg | ME6211 3.3V LDO | Ultra-low quiescent current (40uA) |
| Display (optional) | SSD1306 0.96" OLED | Status display |
| Enclosure | 3D printed (STL files in hardware/) | Wrist-mount or clip-on |

### Power Budget

| Mode | Current | Duration on 1000mAh |
|------|---------|---------------------|
| Active (WiFi AP + Web IDE) | ~120mA | 8 hours |
| Mesh relay (ESP-NOW only) | ~20mA | 50 hours |
| Deep sleep (wake on timer) | ~10uA | Years |
| Mesh sleep (wake every 30s) | ~0.5mA avg | 83 days |

## Quick Start

### 1. Flash the firmware
```bash
# Install ESP-IDF v5.x (https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/)
idf.py set-target esp32s3
idf.py build
idf.py flash
```

### 2. Connect from iPhone
- Join WiFi: `SolarpunkNode-XXXX` (no password)
- Safari opens automatically (captive portal)
- You're in the web IDE -- start coding

### 3. Mesh networking
- Power on 2+ devices near each other
- They auto-discover within seconds via ESP-NOW
- Send messages, share scripts, relay data between nodes

## Architecture

```
iPhone Safari
  |
  | WiFi AP (captive portal)
  v
+--------------------------------------------------+
|  ESP32-S3 Node                                   |
|                                                  |
|  +------------+ +------------+ +---------------+ |
|  | Web Server | | Script     | | Power Manager | |
|  | HTTP + WS  | | Engine     | | Solar + Sleep | |
|  +------------+ +------------+ +---------------+ |
|  +----------------------------------------------+|
|  | Mesh Network (ESP-NOW)                       | |
|  | Auto-discovery, multi-hop relay              | |
|  +----------------------------------------------+|
+--------------------------------------------------+
        ^  ESP-NOW (250m, no router)
        |
+--------------------------------------------------+
|  Other Solarpunk Nodes (auto-discovered)         |
+--------------------------------------------------+
```

## Project Structure

```
main/                       # Firmware source
  main.cpp                  # Entry point, task startup
  config.h                  # All configuration in one place
  web/
    webserver.cpp/h         # HTTP server + WebSocket
    captive.cpp/h           # Captive portal (auto-open on iPhone)
    static/
      index.html            # Web IDE (CodeMirror editor + terminal)
      style.css             # Mobile-first dark theme
      app.js                # Editor logic, WebSocket client
  mesh/
    mesh.cpp/h              # ESP-NOW mesh networking
    discovery.cpp/h         # Auto-discovery + routing
    protocol.h              # Message types and formats
  power/
    solar.cpp/h             # Battery + solar monitoring (ADC)
    sleep.cpp/h             # Deep sleep, wake scheduling
  scripting/
    engine.cpp/h            # Lightweight script runner
  hal/
    uart.cpp/h              # Serial I/O
    gpio.cpp/h              # Pin control
hardware/
  schematic/                # KiCad PCB files
  enclosure/                # 3D printable STL files
  bom.csv                   # Bill of materials with prices
docs/
  getting-started.md
  mesh-protocol.md
  power-budget.md
CMakeLists.txt              # ESP-IDF build system
LICENSE                     # MIT
```

## Mesh Protocol

Devices use ESP-NOW (peer-to-peer, no router, 250m range):

- **Discovery**: Beacon broadcast every 10s -- node ID, battery %, GPS (if available)
- **Routing**: Automatic multi-hop, each node maintains a neighbor table
- **Sleep sync**: Nodes agree on wake windows to save power
- **Messages**: Text chat, file sync, sensor data, remote script deploy
- **Security**: AES-128 encrypted payloads, node allowlists optional

## Low Power Design

The firmware aggressively manages power:
1. **Adaptive WiFi**: AP only activates when iPhone is nearby (BLE scan)
2. **Mesh duty cycle**: ESP-NOW wake every 30s, listen for 50ms, sleep rest
3. **Solar tracking**: ADC monitors panel voltage, adjusts behavior at low light
4. **Task shedding**: Non-essential tasks disabled below 20% battery
5. **Deep sleep**: Full shutdown with RTC wake after prolonged inactivity

## License

MIT License -- build whatever you want.

## Contributing

PRs welcome. Open an issue first for big changes.
