# Solarpunk Computing

A minimal bare-metal Web3 microkernel OS built from scratch in Assembly and C++ for the Raspberry Pi Pico 2 (RP2350) and ESP32.

## Architecture

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

## Components

- **boot/** - Assembly startup code for each target
- **kernel/** - Cooperative task scheduler, memory pool allocator, syscall interface
- **net/** - Minimal TCP/IP stack and WiFi driver
- **web3/** - Ethereum JSON-RPC server, Keccak-256 hashing, transaction types
- **container/** - Lightweight process isolation (sandboxed task containers)
- **terminal/** - Interactive shell over UART
- **drivers/** - Hardware abstraction (UART, GPIO, SPI)
- **linker/** - Linker scripts per target
- **test/** - Unit tests (host-compiled)

## Targets

| Target | MCU | Architecture | RAM | Flash |
|--------|-----|-------------|-----|-------|
| Pi Pico 2 | RP2350 | ARM Cortex-M33 (dual core) | 520KB | 4MB |
| ESP32 | ESP32-WROOM | Xtensa LX6 (dual core) | 520KB | 4MB |

## Build

```bash
# Pi Pico 2
make TARGET=pico2

# ESP32
make TARGET=esp32

# Run tests (host)
make test
```

## License

MIT
