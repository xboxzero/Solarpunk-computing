# How To Guide

Step-by-step instructions for installing, setting up, using, and connecting Solarpunk Computing OS.

---

## 1. Installation

### Prerequisites

- **Hardware**: Raspberry Pi Pico 2 (RP2350) or ESP32-WROOM
- **Toolchain** (pick one based on your target):
  - **Pi Pico 2**: `arm-none-eabi-gcc` (ARM GNU toolchain)
  - **ESP32**: `xtensa-esp32-elf-gcc` (Espressif toolchain)
- **Tools**: `make`, `git`

### Install the Toolchain

**Pi Pico 2 (ARM)**:
```bash
# Debian/Ubuntu
sudo apt install gcc-arm-none-eabi binutils-arm-none-eabi

# macOS (Homebrew)
brew install arm-none-eabi-gcc
```

**ESP32 (Xtensa)**:
```bash
# Follow Espressif's guide to install the toolchain:
# https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/
# After install, make sure xtensa-esp32-elf-gcc is on your PATH.
```

### Clone the Repository

```bash
git clone https://github.com/xboxzero/Solarpunk-computing.git
cd Solarpunk-computing
```

---

## 2. Building

### Build for Pi Pico 2

```bash
make TARGET=pico2
```

This produces:
- `solarpunk-pico2.elf` — ELF binary
- `solarpunk-pico2.bin` — Raw binary for flashing
- `solarpunk-pico2.hex` — Intel HEX format

### Build for ESP32

```bash
make TARGET=esp32
```

This produces:
- `solarpunk-esp32.elf`
- `solarpunk-esp32.bin`
- `solarpunk-esp32.hex`

### Build and Run Tests (Host)

```bash
make test
```

Runs unit tests for memory management, Web3, and containers on your host machine (no hardware needed).

### Clean Build Artifacts

```bash
make clean
```

---

## 3. Flashing

### Pi Pico 2

1. Hold the **BOOTSEL** button on the Pico 2 and plug it into USB.
2. It mounts as a USB mass storage device.
3. Copy the binary:
   ```bash
   cp solarpunk-pico2.bin /media/$USER/RPI-RP2/
   ```
   The board reboots automatically.

Alternatively, use OpenOCD or picotool:
```bash
picotool load solarpunk-pico2.elf
picotool reboot
```

### ESP32

Use `esptool.py`:
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 \
    write_flash 0x1000 solarpunk-esp32.bin
```

---

## 4. Setup and Usage

### Connecting via UART Terminal

The OS provides an interactive shell over UART. Connect with a serial terminal:

```bash
# Linux
screen /dev/ttyACM0 115200

# or with minicom
minicom -b 115200 -D /dev/ttyACM0

# macOS
screen /dev/cu.usbmodem* 115200
```

You should see:
```
Solarpunk Terminal v0.1
Type 'help' for commands.
sp>
```

### Example: Boot and Usage

Here's what it looks like when the OS boots and you interact with it over UART:

```
[boot] Solarpunk Computing OS
[boot] Platform: RP2350 (ARM Cortex-M33)
[boot] CPU: 125 MHz | RAM: 520 KB
[kernel] Initializing kernel...
[kernel] Memory pool: 131072 bytes
[kernel] Scheduler started (max 16 tasks)
[net] Pico2 network init (SPI)...
[net] Network stack initialized
[net] Network task running
[web3] JSON-RPC server listening on port 8545

Solarpunk Terminal v0.1
Type 'help' for commands.
sp> info
Platform:    pico2
Uptime:      12s
CPU:         125 MHz
Tasks:       4
Free memory: 98304 bytes
sp> mem
Heap used: 32768 / 131072 bytes (98304 free)
sp> containers
ID  State    Net  GPIO  Name
--  -------  ---  ----  ----
sp> create myapp
sp> containers
ID  State    Net  GPIO  Name
--  -------  ---  ----  ----
0   created  no   no    myapp
sp> hash hello
0x1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8
sp> tasks
ID  State    Pri  Container  Name
--  -------  ---  ---------  ----
0   running  0    -          kernel
1   running  1    -          net
2   running  1    -          web3
3   running  1    -          terminal
sp> block
Block number: 0
sp>
```

### Shell Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `info` | System information (platform, uptime, CPU, tasks, memory) |
| `mem` | Memory usage (heap used/free) |
| `tasks` | List running tasks |
| `containers` | List all containers with state, permissions |
| `create <name>` | Create a new container |
| `stop <id>` | Stop a container by ID |
| `destroy <id>` | Destroy a container by ID |
| `hash <text>` | Compute Keccak-256 hash of text |
| `block` | Show current block number |
| `reboot` | Reboot the system |

### Containers

Containers provide lightweight process isolation. Each container gets:
- Up to **16KB** of isolated memory
- Up to **4 tasks** running inside it
- Configurable **network** and **GPIO** access permissions

```
sp> create myapp
sp> containers
ID  State    Net  GPIO  Name
--  -------  ---  ----  ----
0   running  no   no    myapp
sp> stop 0
sp> destroy 0
```

---

## 5. Networking

### Network Stack

The OS includes a minimal TCP/IP stack with support for up to **4 concurrent sockets**.

- **Pi Pico 2**: Uses an external SPI-connected Ethernet or WiFi module.
- **ESP32**: Uses the built-in WiFi hardware.

The network initializes automatically at boot. Default IP: `192.168.1.100`.

### Hardware Wiring (Pi Pico 2)

For SPI-based network modules (e.g., W5500 Ethernet or ESP-01 WiFi):

| Pico 2 Pin | Module Pin |
|------------|------------|
| SPI0 SCK (GPIO 18) | SCK |
| SPI0 MOSI (GPIO 19) | MOSI |
| SPI0 MISO (GPIO 16) | MISO |
| SPI0 CS (GPIO 17) | CS |
| 3V3 | VCC |
| GND | GND |

### ESP32 WiFi

The ESP32 uses its onboard WiFi. Configuration is done through the WiFi peripheral registers at boot.

---

## 6. Connectivity — Web3 JSON-RPC

The OS runs an Ethereum-compatible JSON-RPC server on **port 8545**.

### Supported RPC Methods

| Method | Description |
|--------|-------------|
| `eth_blockNumber` | Get current block number |
| `eth_getBalance` | Get account balance |
| `eth_sendTransaction` | Send a transaction |
| `eth_getBlockByNumber` | Get block by number |
| `eth_chainId` | Get chain ID |
| `net_version` | Get network version |
| `web3_clientVersion` | Get client version string |
| `sp_systemInfo` | (Custom) Get system info |
| `sp_containerList` | (Custom) List containers |

### Example: Query from Another Machine

Once the device is on the network, you can interact with it using standard Web3 tools:

```bash
# Using curl
curl -X POST http://192.168.1.100:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Using cast (Foundry)
cast block-number --rpc-url http://192.168.1.100:8545

# System info (custom method)
curl -X POST http://192.168.1.100:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"sp_systemInfo","params":[],"id":1}'
```

### Container Network Permissions

Containers must be explicitly granted network access:
- By default, new containers have `net_allowed = false`
- Enable network access per-container through the container runtime API
- The kernel checks permissions on every network syscall

---

## 7. Architecture Overview

```
+--------------------------------------------------+
|                  Terminal Shell                    |
+--------------------------------------------------+
|          Container Runtime (Isolation)            |
+--------------------------------------------------+
|    Web3 JSON-RPC Server  |  Network Stack (TCP)   |
+--------------------------------------------------+
|         Kernel (Scheduler + Memory Mgmt)          |
+--------------------------------------------------+
|   Drivers (UART, GPIO, SPI, WiFi)                 |
+--------------------------------------------------+
|         Boot (ARM Cortex-M33 / Xtensa)            |
+--------------------------------------------------+
|         Hardware (Pi Pico 2 / ESP32)              |
+--------------------------------------------------+
```

- **Kernel**: Cooperative task scheduler (up to 16 tasks), pool-based memory allocator (128KB heap), 1ms system tick
- **Drivers**: UART (serial I/O), GPIO (pin control), SPI (peripheral communication)
- **Network**: Minimal TCP/IP with 4 sockets, 1KB RX/TX buffers each
- **Web3**: Ethereum JSON-RPC on port 8545, Keccak-256 hashing, transaction/block types
- **Containers**: Up to 8 containers, 16KB memory each, per-container permission model
- **Terminal**: Interactive UART shell with system management commands

---

## License

MIT
