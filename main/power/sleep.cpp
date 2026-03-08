// Solarpunk Wearable - Sleep Manager
// Handles idle detection and deep sleep entry.
// Key power saving strategy:
//   - No clients for 10min -> deep sleep
//   - Mesh-sleep mode: wake 50ms every 30s to check for messages
//   - Critical battery: long deep sleep until solar recharges

#include "sleep.h"
#include "../config.h"
#include "../web/webserver.h"

#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char* TAG = "sleep";

static int64_t last_activity_us = 0;

void sleep_init() {
    last_activity_us = esp_timer_get_time();
    ESP_LOGI(TAG, "Sleep manager init (idle timeout: %ds)",
             SP_IDLE_SLEEP_MS / 1000);
}

void sleep_reset_idle() {
    last_activity_us = esp_timer_get_time();
}

void sleep_check_idle() {
    // Don't sleep if WebSocket clients are connected
    if (ws_client_count() > 0) {
        sleep_reset_idle();
        return;
    }

    int64_t idle_us = esp_timer_get_time() - last_activity_us;
    if (idle_us > (int64_t)SP_IDLE_SLEEP_MS * 1000) {
        ESP_LOGI(TAG, "Idle timeout -- entering mesh-sleep mode");
#if SP_MESH_SLEEP_ENABLED
        sleep_enter_mesh_sleep();
#else
        sleep_enter_deep(SP_DEEP_SLEEP_US);
#endif
    }
}

void sleep_enter_deep(uint64_t duration_us) {
    ESP_LOGI(TAG, "Deep sleep for %llu seconds", duration_us / 1000000ULL);
    esp_sleep_enable_timer_wakeup(duration_us);
    esp_deep_sleep_start();
    // Does not return
}

void sleep_enter_mesh_sleep() {
    ESP_LOGI(TAG, "Mesh-sleep: wake every %ds for %dms",
             (int)(SP_DEEP_SLEEP_US / 1000000), SP_LISTEN_WINDOW_MS);
    esp_sleep_enable_timer_wakeup(SP_DEEP_SLEEP_US);
    esp_deep_sleep_start();
    // On wake, main.cpp detects timer wakeup and does quick mesh listen
}
