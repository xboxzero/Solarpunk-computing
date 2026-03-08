// Solarpunk Wearable - Script Engine v2
// Unified command interpreter - everything runs through here
// Terminal, web API, mesh exec, and LLM agent all use this

#include "engine.h"
#include "../config.h"
#include "../mesh/mesh.h"
#include "../power/solar.h"
#include "../power/sleep.h"
#include "../hal/gpio.h"
#include "../llm/llm_client.h"
#include "../security/crypto.h"

#include "esp_system.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_spiffs.h"
#include "driver/gpio.h"

#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <dirent.h>
#include <sys/stat.h>

static const char* TAG = "engine";

void engine_init() {
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

    ESP_LOGI(TAG, "Script engine v2 ready");
}

// Parse and execute a command, write output to buf
int engine_run(const char* script, char* output, int output_size) {
    if (!script || !output || output_size < 2) return -1;
    output[0] = '\0';

    while (*script == ' ' || *script == '\n' || *script == '\r') script++;
    if (*script == '\0') return 0;

    // === System Commands ===

    if (strcmp(script, "help") == 0) {
        snprintf(output, output_size,
            "system:  status, free, uptime, reboot, version\\n"
            "io:      gpio <pin> <0|1>, read <pin>, adc <pin>\\n"
            "mesh:    peers, send <msg>, send @<node> <msg>\\n"
            "         exec @<node> <cmd>, whoami\\n"
            "files:   ls, cat <file>, write <file> <content>, rm <file>\\n"
            "ai:      ask <question>, agent <task>\\n"
            "power:   battery, solar, sleep <sec>\\n"
            "security: token, encrypt-status\\n"
        );
        return 0;
    }

    if (strcmp(script, "status") == 0) {
        char node_name[16];
        mesh_get_self_name(node_name, sizeof(node_name));
        snprintf(output, output_size,
            "%s v%s\\n"
            "battery: %d%% (%dmV)\\n"
            "solar:   %dmV %s\\n"
            "peers:   %d\\n"
            "heap:    %lu bytes\\n"
            "uptime:  %llds\\n"
            "encrypt: %s",
            node_name, SP_FIRMWARE_VERSION,
            solar_battery_percent(), solar_battery_mv(),
            solar_panel_mv(), solar_is_charging() ? "(charging)" : "",
            mesh_peer_count(),
            (unsigned long)esp_get_free_heap_size(),
            esp_timer_get_time() / 1000000LL,
            SP_MESH_ENCRYPT ? "AES-256-GCM" : "off");
        return 0;
    }

    if (strcmp(script, "version") == 0) {
        snprintf(output, output_size, "solarpunk v%s", SP_FIRMWARE_VERSION);
        return 0;
    }

    if (strcmp(script, "whoami") == 0) {
        char name[16];
        mesh_get_self_name(name, sizeof(name));
        uint8_t mac[6];
        mesh_get_self_mac(mac);
        snprintf(output, output_size, "%s (%02X:%02X:%02X:%02X:%02X:%02X)",
                 name, mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        return 0;
    }

    // === AI Commands ===

    if (strncmp(script, "ask ", 4) == 0) {
        const char* question = script + 4;
        if (strlen(question) == 0) {
            snprintf(output, output_size, "usage: ask <question>");
            return -1;
        }
        return llm_ask(question, output, output_size);
    }

    if (strncmp(script, "agent ", 6) == 0) {
        const char* task = script + 6;
        if (strlen(task) == 0) {
            snprintf(output, output_size, "usage: agent <task description>");
            return -1;
        }
        return llm_agent(task, output, output_size);
    }

    // === Mesh Commands ===

    if (strcmp(script, "peers") == 0) {
        mesh_peers_json(output, output_size);
        return 0;
    }

    if (strncmp(script, "send ", 5) == 0) {
        const char* arg = script + 5;

        // send @node message
        if (arg[0] == '@') {
            const char* space = strchr(arg + 1, ' ');
            if (space) {
                char node_name[16];
                int nlen = space - arg - 1;
                if (nlen >= (int)sizeof(node_name)) nlen = sizeof(node_name) - 1;
                memcpy(node_name, arg + 1, nlen);
                node_name[nlen] = '\0';

                const char* msg = space + 1;
                uint8_t mac[6];
                if (mesh_find_by_name(node_name, mac)) {
                    mesh_send_to(mac, msg, strlen(msg));
                    snprintf(output, output_size, "sent to %s", node_name);
                } else {
                    snprintf(output, output_size, "node not found: %s", node_name);
                    return -1;
                }
            } else {
                snprintf(output, output_size, "usage: send @<node> <message>");
                return -1;
            }
        } else {
            // Broadcast
            mesh_broadcast(arg, strlen(arg));
            snprintf(output, output_size, "broadcast to %d peers", mesh_peer_count());
        }
        return 0;
    }

    if (strncmp(script, "exec @", 6) == 0) {
        const char* arg = script + 6;
        const char* space = strchr(arg, ' ');
        if (space) {
            char node_name[16];
            int nlen = space - arg;
            if (nlen >= (int)sizeof(node_name)) nlen = sizeof(node_name) - 1;
            memcpy(node_name, arg, nlen);
            node_name[nlen] = '\0';

            const char* cmd = space + 1;
            mesh_exec_remote(node_name, cmd);
            snprintf(output, output_size, "exec '%s' on %s (async)", cmd, node_name);
        } else {
            snprintf(output, output_size, "usage: exec @<node> <command>");
            return -1;
        }
        return 0;
    }

    // === GPIO / ADC ===

    if (strncmp(script, "gpio ", 5) == 0) {
        int pin = 0, val = 0;
        if (sscanf(script + 5, "%d %d", &pin, &val) == 2) {
            solarpunk::gpio_init(pin, solarpunk::GpioDir::OUTPUT);
            solarpunk::gpio_set(pin, val != 0);
            snprintf(output, output_size, "GPIO %d = %d", pin, val);
            return 0;
        }
        snprintf(output, output_size, "usage: gpio <pin> <0|1>");
        return -1;
    }

    if (strncmp(script, "read ", 5) == 0) {
        int pin = atoi(script + 5);
        solarpunk::gpio_init(pin, solarpunk::GpioDir::INPUT);
        int val = solarpunk::gpio_get(pin) ? 1 : 0;
        snprintf(output, output_size, "GPIO %d = %d", pin, val);
        return 0;
    }

    if (strncmp(script, "adc ", 4) == 0) {
        int pin = atoi(script + 4);
        // Use the solar module's cached readings for battery/solar pins
        if (pin == SP_BATTERY_ADC_PIN) {
            snprintf(output, output_size, "ADC ch%d (battery): %dmV", pin, solar_battery_mv());
        } else if (pin == SP_SOLAR_ADC_PIN) {
            snprintf(output, output_size, "ADC ch%d (solar): %dmV", pin, solar_panel_mv());
        } else {
            snprintf(output, output_size, "ADC ch%d: use battery(ch%d) or solar(ch%d)",
                     pin, SP_BATTERY_ADC_PIN, SP_SOLAR_ADC_PIN);
        }
        return 0;
    }

    // === File Commands ===

    if (strcmp(script, "ls") == 0) {
        DIR* dir = opendir(SP_SCRIPT_STORAGE);
        if (!dir) {
            snprintf(output, output_size, "(no files)");
            return 0;
        }
        int pos = 0;
        struct dirent* ent;
        while ((ent = readdir(dir)) != NULL) {
            // Get file size
            char path[128];
            snprintf(path, sizeof(path), "%s/%.96s", SP_SCRIPT_STORAGE, ent->d_name);
            struct stat st;
            int size = 0;
            if (stat(path, &st) == 0) size = st.st_size;
            pos += snprintf(output + pos, output_size - pos, "  %s (%d bytes)\\n",
                           ent->d_name, size);
        }
        closedir(dir);
        if (pos == 0) snprintf(output, output_size, "(no files)");
        return 0;
    }

    if (strncmp(script, "cat ", 4) == 0) {
        const char* fname = script + 4;
        char path[64];
        snprintf(path, sizeof(path), "%s/%s", SP_SCRIPT_STORAGE, fname);
        FILE* f = fopen(path, "r");
        if (!f) {
            snprintf(output, output_size, "file not found: %s", fname);
            return -1;
        }
        int n = fread(output, 1, output_size - 1, f);
        output[n] = '\0';
        fclose(f);
        return 0;
    }

    if (strncmp(script, "write ", 6) == 0) {
        const char* arg = script + 6;
        const char* space = strchr(arg, ' ');
        if (!space) {
            snprintf(output, output_size, "usage: write <filename> <content>");
            return -1;
        }
        char fname[32];
        int nlen = space - arg;
        if (nlen >= (int)sizeof(fname)) nlen = sizeof(fname) - 1;
        memcpy(fname, arg, nlen);
        fname[nlen] = '\0';

        const char* content = space + 1;
        char path[64];
        snprintf(path, sizeof(path), "%s/%s", SP_SCRIPT_STORAGE, fname);
        FILE* f = fopen(path, "w");
        if (!f) {
            snprintf(output, output_size, "cannot write: %s", fname);
            return -1;
        }
        // Replace \\n with real newlines for multi-line content
        while (*content) {
            if (content[0] == '\\' && content[1] == 'n') {
                fputc('\n', f);
                content += 2;
            } else {
                fputc(*content, f);
                content++;
            }
        }
        fclose(f);
        snprintf(output, output_size, "saved: %s", fname);
        return 0;
    }

    if (strncmp(script, "rm ", 3) == 0) {
        const char* fname = script + 3;
        char path[64];
        snprintf(path, sizeof(path), "%s/%s", SP_SCRIPT_STORAGE, fname);
        if (remove(path) == 0) {
            snprintf(output, output_size, "deleted: %s", fname);
        } else {
            snprintf(output, output_size, "not found: %s", fname);
            return -1;
        }
        return 0;
    }

    // === Power Commands ===

    if (strcmp(script, "battery") == 0) {
        snprintf(output, output_size, "%d%% (%dmV) %s",
                 solar_battery_percent(), solar_battery_mv(),
                 solar_is_charging() ? "charging" : "discharging");
        return 0;
    }

    if (strcmp(script, "solar") == 0) {
        snprintf(output, output_size, "%dmV %s",
                 solar_panel_mv(), solar_is_charging() ? "(active)" : "(dark)");
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
        snprintf(output, output_size, "rebooting...");
        esp_restart();
        return 0;
    }

    if (strncmp(script, "sleep ", 6) == 0) {
        int secs = atoi(script + 6);
        if (secs > 0) {
            snprintf(output, output_size, "sleeping %ds...", secs);
            sleep_enter_deep((uint64_t)secs * 1000000ULL);
            return 0;  // Won't reach here
        }
        snprintf(output, output_size, "usage: sleep <seconds>");
        return -1;
    }

    // === Security Commands ===

    if (strcmp(script, "token") == 0) {
        snprintf(output, output_size, "auth: %s", crypto_get_token());
        return 0;
    }

    if (strcmp(script, "encrypt-status") == 0) {
        snprintf(output, output_size,
            "mesh: %s\\nauth: %s\\nkey: %d-bit",
            SP_MESH_ENCRYPT ? "AES-256-GCM" : "off",
            SP_AUTH_ENABLED ? "enabled" : "disabled",
            SP_MESH_KEY_LEN * 8);
        return 0;
    }

    // Unknown command
    snprintf(output, output_size, "unknown: %s\\ntype 'help' for commands", script);
    return -1;
}
