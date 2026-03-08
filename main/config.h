#pragma once

// ============================================================
// Solarpunk Wearable Computer - Configuration
// All tunable parameters in one place
// ============================================================

// --- Device Identity ---
#define SP_DEVICE_NAME          "SolarpunkNode"
#define SP_FIRMWARE_VERSION     "0.3.0"

// --- WiFi Access Point ---
#define SP_WIFI_CHANNEL         1
#define SP_WIFI_MAX_CLIENTS     4       // Allow more clients for mesh admin
#define SP_WIFI_AP_INACTIVE_MS  300000  // Disable AP after 5min no clients

// --- Web Server ---
#define SP_HTTP_PORT            80
#define SP_WS_PORT              81      // WebSocket for terminal
#define SP_MAX_WS_CLIENTS       4
#define SP_MAX_SCRIPT_SIZE      8192    // Max script upload size

// --- Security ---
#define SP_AUTH_ENABLED         1       // Require auth token for API
#define SP_AUTH_TOKEN           "solarpunk2026"  // Change this! Used for API auth
#define SP_MESH_KEY             "SolarpunkMeshKey!SolarpunkMeshKey!"  // 32-byte AES-256 key
#define SP_MESH_KEY_LEN         32
#define SP_CRYPTO_IV_LEN        12      // GCM IV length
#define SP_CRYPTO_TAG_LEN       16      // GCM auth tag length

// --- Mesh Network (ESP-NOW) ---
#define SP_MESH_CHANNEL         1
#define SP_MESH_BEACON_MS       10000   // Beacon interval
#define SP_MESH_MAX_PEERS       16      // Max discovered nodes
#define SP_MESH_MAX_HOPS        6       // Multi-hop relay limit (increased for 3+ nodes)
#define SP_MESH_MSG_SIZE        200     // ESP-NOW max is 250 bytes
#define SP_MESH_ENCRYPT         1       // AES-256-GCM encryption
#define SP_MESH_PMK             "solarpunk-mesh!"  // ESP-NOW PMK (16 chars)
#define SP_MESH_PEER_EXPIRE_MS  90000   // Expire peers after 90s (was 60s)

// --- Power Management ---
#define SP_BATTERY_ADC_PIN      4       // ADC pin for battery voltage divider
#define SP_SOLAR_ADC_PIN        5       // ADC pin for solar panel voltage
#define SP_BATTERY_FULL_MV      4200    // Full charge voltage
#define SP_BATTERY_EMPTY_MV     3200    // Empty voltage (protect LiPo)
#define SP_BATTERY_LOW_PCT      20      // Low battery threshold
#define SP_BATTERY_CRITICAL_PCT 10      // Critical -- disable non-essential

// --- Sleep ---
#define SP_DEEP_SLEEP_US        30000000  // 30s deep sleep in mesh-sleep mode
#define SP_LISTEN_WINDOW_MS     50        // Listen window after wake
#define SP_IDLE_SLEEP_MS        600000    // Sleep after 10min idle (no clients)
#define SP_MESH_SLEEP_ENABLED   1         // Enable coordinated mesh sleep

// --- Target ---
// Supports both ESP32 (original) and ESP32-S3
// Set target with: idf.py set-target esp32   (or esp32s3)

// --- GPIO Pins ---
#define SP_LED_PIN              2         // Onboard LED
#define SP_OLED_SDA             21        // I2C SDA for optional OLED
#define SP_OLED_SCL             22        // I2C SCL for optional OLED
#define SP_CHARGE_STAT_PIN      15        // TP4056 charge status

// --- WiFi Station (connect to Pi server network) ---
#define SP_STA_ENABLED          1         // Enable station mode (AP+STA)
#define SP_STA_SSID             "solarpunk-pi"    // Pi's WiFi network name
#define SP_STA_PASS             "solarpunk"        // Pi's WiFi password
#define SP_STA_RETRY_MAX        10        // Max connection retries

// --- LLM Server (Pi 5) ---
#define SP_LLM_HOST             "10.42.0.1"       // Pi's hotspot IP
#define SP_LLM_PORT             8080              // llama.cpp server port
#define SP_LLM_TIMEOUT_MS       30000             // Response timeout
#define SP_LLM_MAX_TOKENS       512               // Max response tokens (increased for agent)
#define SP_AGENT_MAX_ITERS      5                 // Max agent command iterations
#define SP_AGENT_MAX_CMDS       8                 // Max commands per agent iteration

// --- Scripting ---
#define SP_SCRIPT_STORAGE       "/spiffs/scripts"
#define SP_MAX_SCRIPTS          16
#define SP_SCRIPT_TIMEOUT_MS    5000      // Kill runaway scripts

// --- Display (optional SSD1306) ---
#define SP_DISPLAY_ENABLED      0
#define SP_DISPLAY_WIDTH        128
#define SP_DISPLAY_HEIGHT       64
