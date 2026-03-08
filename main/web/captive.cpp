// Solarpunk Wearable - Captive Portal
// DNS server that redirects all queries to our AP IP.
// iPhone detects this and auto-opens Safari to our web IDE.

#include "captive.h"
#include "../config.h"

#include "esp_log.h"
#include "esp_netif.h"
#include "lwip/sockets.h"
#include "lwip/dns.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include <cstring>

static const char* TAG = "captive";
static TaskHandle_t dns_task_handle = NULL;
static bool running = false;

// Minimal DNS response: redirect everything to our AP IP (192.168.4.1)
static void dns_server_task(void* arg) {
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Failed to create DNS socket");
        vTaskDelete(NULL);
        return;
    }

    struct sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(53);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        ESP_LOGE(TAG, "DNS bind failed");
        close(sock);
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "Captive DNS started -- all domains -> 192.168.4.1");

    uint8_t buf[512];
    struct sockaddr_in client;
    socklen_t client_len;

    while (running) {
        client_len = sizeof(client);
        int len = recvfrom(sock, buf, sizeof(buf), 0,
                           (struct sockaddr*)&client, &client_len);
        if (len < 12) continue;

        // Build DNS response: copy query, set response flags, add answer
        uint8_t resp[512];
        memcpy(resp, buf, len);

        // Set QR=1 (response), AA=1 (authoritative)
        resp[2] = 0x84;
        resp[3] = 0x00;
        // ANCOUNT = 1
        resp[6] = 0x00;
        resp[7] = 0x01;

        // Append answer: pointer to query name + A record -> 192.168.4.1
        int pos = len;
        resp[pos++] = 0xC0;  // Name pointer
        resp[pos++] = 0x0C;  // Offset to query name
        resp[pos++] = 0x00; resp[pos++] = 0x01;  // Type A
        resp[pos++] = 0x00; resp[pos++] = 0x01;  // Class IN
        resp[pos++] = 0x00; resp[pos++] = 0x00;
        resp[pos++] = 0x00; resp[pos++] = 0x0A;  // TTL = 10s
        resp[pos++] = 0x00; resp[pos++] = 0x04;  // Data length = 4
        resp[pos++] = 192; resp[pos++] = 168;
        resp[pos++] = 4;   resp[pos++] = 1;      // 192.168.4.1

        sendto(sock, resp, pos, 0,
               (struct sockaddr*)&client, client_len);
    }

    close(sock);
    vTaskDelete(NULL);
}

void captive_init() {
    running = true;
    xTaskCreate(dns_server_task, "dns", 4096, NULL, 3, &dns_task_handle);
}

void captive_stop() {
    running = false;
}
