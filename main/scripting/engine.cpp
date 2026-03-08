// Solarpunk Wearable - Script Engine
// Simple command interpreter for the web IDE terminal.
// Supports basic system commands + GPIO control.
// Designed to be extended with MicroPython or Duktape JS later.

#include "engine.h"
#include "../config.h"
#include "../mesh/mesh.h"
#include "../power/solar.h"
#include "../hal/gpio.h"

#include "esp_system.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_spiffs.h"

#include <cstring>
#include <cstdio>
#include <cstdlib>

static const char* TAG = "engine";

void engine_init() {
    // Mount SPIFFS for script storage
    esp_vfs_spiffs_conf_t spiffs_cfg = {
        .base_path = SP_SCRIPT_STORAGE,
        .partition_label = NULL,
        .max_files = SP_MAX_SCRIPTS,
        .format_if_mount_failed = true,
    };
    esp_err_t ret = esp_vfs_spiffs_register(&spiffs_cfg);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "SPIFFS mount failed, scripts won't persist");
    }

    ESP_LOGI(TAG, "Script engine ready");
}

// Parse and execute a command, write output to buf
int engine_run(const char* script, char* output, int output_size) {
    if (!script || !output || output_size < 2) return -1;
    output[0] = '\0';

    // Skip whitespace
    while (*script == ' ' || *script == '\n' || *script == '\r') script++;
    if (*script == '\0') return 0;

    // --- Built-in commands ---

    if (strcmp(script, "help") == 0) {
        snprintf(output, output_size,
            "Commands:\\n"
            "  help          - Show this help\\n"
            "  status        - Device status\\n"
            "  peers         - List mesh peers\\n"
            "  send <msg>    - Broadcast to mesh\\n"
            "  gpio <p> <v>  - Set GPIO pin (0/1)\\n"
            "  read <pin>    - Read GPIO pin\\n"
            "  sleep <sec>   - Enter deep sleep\\n"
            "  reboot        - Restart device\\n"
            "  free          - Free heap memory\\n"
            "  uptime        - System uptime\\n"
            "  ls            - List saved scripts\\n"
            "  save <name>   - Save last script\\n"
        );
        return 0;
    }

    if (strcmp(script, "status") == 0) {
        snprintf(output, output_size,
            "Battery: %d%% (%dmV)\\n"
            "Solar: %dmV %s\\n"
            "Peers: %d\\n"
            "Heap: %lu bytes free\\n"
            "Uptime: %llds\\n"
            "Firmware: %s",
            solar_battery_percent(), solar_battery_mv(),
            solar_panel_mv(), solar_is_charging() ? "(charging)" : "",
            mesh_peer_count(),
            (unsigned long)esp_get_free_heap_size(),
            esp_timer_get_time() / 1000000LL,
            SP_FIRMWARE_VERSION);
        return 0;
    }

    if (strcmp(script, "peers") == 0) {
        mesh_peers_json(output, output_size);
        return 0;
    }

    if (strncmp(script, "send ", 5) == 0) {
        const char* msg = script + 5;
        mesh_broadcast(msg, strlen(msg));
        snprintf(output, output_size, "Sent to %d peers", mesh_peer_count());
        return 0;
    }

    if (strncmp(script, "gpio ", 5) == 0) {
        int pin = 0, val = 0;
        if (sscanf(script + 5, "%d %d", &pin, &val) == 2) {
            solarpunk::gpio_init(pin, solarpunk::GpioDir::OUTPUT);
            solarpunk::gpio_set(pin, val != 0);
            snprintf(output, output_size, "GPIO %d = %d", pin, val);
            return 0;
        }
        snprintf(output, output_size, "Usage: gpio <pin> <0|1>");
        return -1;
    }

    if (strncmp(script, "read ", 5) == 0) {
        int pin = atoi(script + 5);
        solarpunk::gpio_init(pin, solarpunk::GpioDir::INPUT);
        int val = solarpunk::gpio_get(pin) ? 1 : 0;
        snprintf(output, output_size, "GPIO %d = %d", pin, val);
        return 0;
    }

    if (strcmp(script, "free") == 0) {
        snprintf(output, output_size, "%lu bytes free",
                 (unsigned long)esp_get_free_heap_size());
        return 0;
    }

    if (strcmp(script, "uptime") == 0) {
        int64_t up = esp_timer_get_time() / 1000000LL;
        int h = up / 3600;
        int m = (up % 3600) / 60;
        int s = up % 60;
        snprintf(output, output_size, "%dh %dm %ds", h, m, s);
        return 0;
    }

    if (strcmp(script, "reboot") == 0) {
        snprintf(output, output_size, "Rebooting...");
        esp_restart();
        return 0;
    }

    if (strncmp(script, "sleep ", 6) == 0) {
        int secs = atoi(script + 6);
        if (secs > 0) {
            snprintf(output, output_size, "Sleeping for %d seconds...", secs);
            // Sleep will happen after response is sent
            return 0;
        }
        snprintf(output, output_size, "Usage: sleep <seconds>");
        return -1;
    }

    // Unknown command
    snprintf(output, output_size, "Unknown command: %s\\nType 'help' for commands", script);
    return -1;
}
