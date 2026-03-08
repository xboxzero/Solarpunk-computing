// Solarpunk Wearable Computer - Main Entry Point
// ESP-IDF application startup

#include "config.h"
#include "web/webserver.h"
#include "web/captive.h"
#include "mesh/mesh.h"
#include "mesh/discovery.h"
#include "power/solar.h"
#include "power/sleep.h"
#include "scripting/engine.h"

#include <cstring>

#include "esp_system.h"
#include "esp_mac.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_sleep.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char* TAG = "solarpunk";

// Generate unique node name from MAC address
static void get_node_name(char* buf, size_t len) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP);
    snprintf(buf, len, "%s-%02X%02X", SP_DEVICE_NAME, mac[4], mac[5]);
}

// Initialize WiFi in AP mode (captive portal for iPhone)
static void wifi_ap_init(const char* ssid) {
    esp_netif_create_default_wifi_ap();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    wifi_config_t wifi_config = {};
    strncpy((char*)wifi_config.ap.ssid, ssid, sizeof(wifi_config.ap.ssid));
    wifi_config.ap.ssid_len = strlen(ssid);
    wifi_config.ap.channel = SP_WIFI_CHANNEL;
    wifi_config.ap.max_connection = SP_WIFI_MAX_CLIENTS;
    wifi_config.ap.authmode = WIFI_AUTH_OPEN;  // No password -- easy iPhone connect

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &wifi_config));

    ESP_ERROR_CHECK(esp_wifi_start());

    // Reduce TX power to save energy (8dBm is enough for nearby phone)
    // Must be called after esp_wifi_start()
    esp_wifi_set_max_tx_power(32);  // 8dBm (units of 0.25dBm)

    ESP_LOGI(TAG, "WiFi AP started: %s (open, ch%d)", ssid, SP_WIFI_CHANNEL);
}

// WiFi event handler
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                                int32_t event_id, void* event_data) {
    if (event_id == WIFI_EVENT_AP_STACONNECTED) {
        wifi_event_ap_staconnected_t* event = (wifi_event_ap_staconnected_t*)event_data;
        ESP_LOGI(TAG, "Client connected (AID=%d)", event->aid);
        // Reset idle timer -- someone is using us
        sleep_reset_idle();
    } else if (event_id == WIFI_EVENT_AP_STADISCONNECTED) {
        ESP_LOGI(TAG, "Client disconnected");
    }
}

extern "C" void app_main(void) {
    ESP_LOGI(TAG, "=================================");
    ESP_LOGI(TAG, "  Solarpunk Wearable Computer");
    ESP_LOGI(TAG, "  Firmware %s", SP_FIRMWARE_VERSION);
    ESP_LOGI(TAG, "=================================");

    // Initialize NVS (required for WiFi)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Initialize event loop
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL);

    // Initialize network interface
    ESP_ERROR_CHECK(esp_netif_init());

    // Check why we woke up (deep sleep resume vs fresh boot)
    esp_sleep_wakeup_cause_t wakeup = esp_sleep_get_wakeup_cause();

    // Initialize power management (must be early -- decides what to enable)
    solar_init();
    sleep_init();

    int battery_pct = solar_battery_percent();
    ESP_LOGI(TAG, "Battery: %d%%", battery_pct);

    // If we woke from mesh-sleep, just do a quick listen and go back to sleep
    if (wakeup == ESP_SLEEP_WAKEUP_TIMER && battery_pct > SP_BATTERY_CRITICAL_PCT) {
        ESP_LOGI(TAG, "Mesh-sleep wake: listening for %dms", SP_LISTEN_WINDOW_MS);
        mesh_init();
        mesh_quick_listen(SP_LISTEN_WINDOW_MS);
        sleep_enter_mesh_sleep();
        return;  // Won't reach here
    }

    // Critical battery -- go to deep sleep until solar charges us
    if (battery_pct <= SP_BATTERY_CRITICAL_PCT) {
        ESP_LOGW(TAG, "Critical battery (%d%%) -- sleeping until charged", battery_pct);
        sleep_enter_deep(SP_DEEP_SLEEP_US * 10);  // Long sleep
        return;
    }

    // Full boot -- start all services
    char node_name[32];
    get_node_name(node_name, sizeof(node_name));
    ESP_LOGI(TAG, "Node: %s", node_name);

    // Start WiFi AP
    wifi_ap_init(node_name);

    // Start captive portal (DNS redirect for iPhone auto-open)
    captive_init();

    // Start web IDE server
    webserver_init();

    // Start mesh networking
    mesh_init();
    discovery_init();

    // Start script engine
    engine_init();

    // Low battery? Disable non-essential features
    if (battery_pct < SP_BATTERY_LOW_PCT) {
        ESP_LOGW(TAG, "Low battery -- reduced functionality");
        // Could disable OLED, reduce beacon rate, etc.
    }

    ESP_LOGI(TAG, "All systems up. Connect to WiFi: %s", node_name);

    // Main loop -- monitor power and idle timeout
    while (1) {
        solar_update();
        sleep_check_idle();
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
