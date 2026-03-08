// Solarpunk Wearable - ESP-NOW Mesh Network
// Zero-config peer-to-peer mesh. No router, no internet.

#include "mesh.h"
#include "protocol.h"
#include "../config.h"
#include "../web/webserver.h"
#include "../power/solar.h"

#include "esp_now.h"
#include "esp_wifi.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include <cstring>
#include <cstdio>

static const char* TAG = "mesh";

// Peer table
static MeshPeer peers[SP_MESH_MAX_PEERS];
static uint16_t msg_seq = 0;
static uint8_t  self_mac[6];

// Recent message sequence numbers for dedup
static uint16_t seen_seqs[64];
static int seen_idx = 0;

static bool is_duplicate(uint16_t seq) {
    for (int i = 0; i < 64; i++) {
        if (seen_seqs[i] == seq) return true;
    }
    seen_seqs[seen_idx] = seq;
    seen_idx = (seen_idx + 1) % 64;
    return false;
}

// Find or add peer by MAC
static MeshPeer* find_peer(const uint8_t* mac) {
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (peers[i].active && memcmp(peers[i].mac, mac, 6) == 0) {
            return &peers[i];
        }
    }
    return NULL;
}

static MeshPeer* add_peer(const uint8_t* mac) {
    // Find empty slot
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (!peers[i].active) {
            memcpy(peers[i].mac, mac, 6);
            peers[i].active = true;
            peers[i].last_seen_ms = esp_timer_get_time() / 1000;

            // Register with ESP-NOW
            esp_now_peer_info_t peer_info = {};
            memcpy(peer_info.peer_addr, mac, 6);
            peer_info.channel = SP_MESH_CHANNEL;
            peer_info.encrypt = false;
            esp_now_add_peer(&peer_info);

            ESP_LOGI(TAG, "New peer: %02X:%02X:%02X:%02X:%02X:%02X",
                     mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
            return &peers[i];
        }
    }
    return NULL;
}

// Handle incoming beacon
static void handle_beacon(const MeshBeacon* beacon, int8_t rssi) {
    if (memcmp(beacon->hdr.src_mac, self_mac, 6) == 0) return;

    MeshPeer* peer = find_peer(beacon->hdr.src_mac);
    if (!peer) {
        peer = add_peer(beacon->hdr.src_mac);
        if (!peer) return;
    }

    strncpy(peer->name, beacon->name, sizeof(peer->name) - 1);
    peer->battery_pct = beacon->battery_pct;
    peer->rssi = rssi;
    peer->hops = beacon->hdr.hops;
    peer->last_seen_ms = esp_timer_get_time() / 1000;
}

// Handle incoming text message
static void handle_text(const MeshText* msg) {
    // Forward to web IDE via WebSocket
    char ws_msg[256];
    snprintf(ws_msg, sizeof(ws_msg), "[mesh:%02X%02X] %.*s",
             msg->hdr.src_mac[4], msg->hdr.src_mac[5],
             msg->len, msg->text);
    ws_broadcast(ws_msg, strlen(ws_msg));
}

// Relay message if hops remaining
static void maybe_relay(const uint8_t* data, int len) {
    if (len < (int)sizeof(MeshHeader)) return;
    MeshHeader* hdr = (MeshHeader*)data;
    if (hdr->hops <= 1) return;

    // Decrement hop count and rebroadcast
    uint8_t relay[250];
    memcpy(relay, data, len);
    ((MeshHeader*)relay)->hops--;

    static const uint8_t broadcast_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    esp_now_send(broadcast_mac, relay, len);
}

// ESP-NOW receive callback
static void on_recv(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
    if (len < (int)sizeof(MeshHeader)) return;

    const MeshHeader* hdr = (const MeshHeader*)data;
    if (hdr->magic != MESH_MAGIC) return;
    if (is_duplicate(hdr->seq)) return;

    // Get RSSI from recv info
    int8_t rssi = 0;  // ESP-NOW provides this in info

    switch (hdr->type) {
    case MESH_BEACON:
        if (len >= (int)sizeof(MeshBeacon)) {
            handle_beacon((const MeshBeacon*)data, rssi);
        }
        break;
    case MESH_TEXT:
        if (len >= (int)sizeof(MeshHeader) + 7) {
            handle_text((const MeshText*)data);
            maybe_relay(data, len);
        }
        break;
    case MESH_PING:
        // Update last_seen for peer
        {
            MeshPeer* p = find_peer(hdr->src_mac);
            if (p) p->last_seen_ms = esp_timer_get_time() / 1000;
        }
        break;
    default:
        maybe_relay(data, len);
        break;
    }
}

// ESP-NOW send callback
static void on_send(const uint8_t* mac, esp_now_send_status_t status) {
    if (status != ESP_NOW_SEND_SUCCESS) {
        ESP_LOGW(TAG, "Send failed to %02X:%02X", mac[4], mac[5]);
    }
}

// Send discovery beacon
static void send_beacon() {
    MeshBeacon beacon = {};
    beacon.hdr.magic = MESH_MAGIC;
    beacon.hdr.version = MESH_VERSION;
    beacon.hdr.type = MESH_BEACON;
    beacon.hdr.hops = SP_MESH_MAX_HOPS;
    memcpy(beacon.hdr.src_mac, self_mac, 6);
    beacon.hdr.seq = msg_seq++;

    beacon.battery_pct = solar_battery_percent();
    beacon.solar_active = solar_is_charging() ? 1 : 0;
    beacon.peer_count = mesh_peer_count();
    beacon.flags = 0;

    // Node name from MAC
    snprintf(beacon.name, sizeof(beacon.name), "SP-%02X%02X",
             self_mac[4], self_mac[5]);

    static const uint8_t broadcast_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    esp_now_send(broadcast_mac, (uint8_t*)&beacon, sizeof(beacon));
}

// Background task: periodic beacons + peer cleanup
static void mesh_task(void* arg) {
    while (1) {
        send_beacon();

        // Expire old peers (not seen for 60s)
        uint32_t now = esp_timer_get_time() / 1000;
        for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
            if (peers[i].active && (now - peers[i].last_seen_ms) > 60000) {
                ESP_LOGI(TAG, "Peer expired: %s", peers[i].name);
                esp_now_del_peer(peers[i].mac);
                peers[i].active = false;
            }
        }

        vTaskDelay(pdMS_TO_TICKS(SP_MESH_BEACON_MS));
    }
}

// --- Public API ---

void mesh_init() {
    esp_read_mac(self_mac, ESP_MAC_WIFI_STA);
    memset(peers, 0, sizeof(peers));

    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_recv));
    ESP_ERROR_CHECK(esp_now_register_send_cb(on_send));

    // Add broadcast peer
    esp_now_peer_info_t broadcast = {};
    memset(broadcast.peer_addr, 0xFF, 6);
    broadcast.channel = SP_MESH_CHANNEL;
    broadcast.encrypt = false;
    esp_now_add_peer(&broadcast);

    xTaskCreate(mesh_task, "mesh", 4096, NULL, 4, NULL);
    ESP_LOGI(TAG, "Mesh network initialized (ESP-NOW, ch%d)", SP_MESH_CHANNEL);
}

void mesh_broadcast(const char* data, int len) {
    MeshText msg = {};
    msg.hdr.magic = MESH_MAGIC;
    msg.hdr.version = MESH_VERSION;
    msg.hdr.type = MESH_TEXT;
    msg.hdr.hops = SP_MESH_MAX_HOPS;
    memcpy(msg.hdr.src_mac, self_mac, 6);
    msg.hdr.seq = msg_seq++;
    memset(msg.dst_mac, 0xFF, 6);

    int copy_len = len;
    if (copy_len > (int)sizeof(msg.text)) copy_len = sizeof(msg.text);
    msg.len = copy_len;
    memcpy(msg.text, data, copy_len);

    static const uint8_t broadcast_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    esp_now_send(broadcast_mac, (uint8_t*)&msg, sizeof(MeshHeader) + 7 + copy_len);
}

void mesh_send_to(const uint8_t* mac, const char* data, int len) {
    MeshText msg = {};
    msg.hdr.magic = MESH_MAGIC;
    msg.hdr.version = MESH_VERSION;
    msg.hdr.type = MESH_TEXT;
    msg.hdr.hops = SP_MESH_MAX_HOPS;
    memcpy(msg.hdr.src_mac, self_mac, 6);
    msg.hdr.seq = msg_seq++;
    memcpy(msg.dst_mac, mac, 6);

    int copy_len = len;
    if (copy_len > (int)sizeof(msg.text)) copy_len = sizeof(msg.text);
    msg.len = copy_len;
    memcpy(msg.text, data, copy_len);

    esp_now_send(mac, (uint8_t*)&msg, sizeof(MeshHeader) + 7 + copy_len);
}

void mesh_quick_listen(int duration_ms) {
    // Used during mesh-sleep wake: listen briefly for incoming messages
    vTaskDelay(pdMS_TO_TICKS(duration_ms));
}

int mesh_peer_count() {
    int count = 0;
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (peers[i].active) count++;
    }
    return count;
}

void mesh_peers_json(char* buf, int buflen) {
    int pos = 0;
    pos += snprintf(buf + pos, buflen - pos, "[");
    bool first = true;
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (!peers[i].active) continue;
        if (!first) pos += snprintf(buf + pos, buflen - pos, ",");
        pos += snprintf(buf + pos, buflen - pos,
            "{\"name\":\"%s\",\"mac\":\"%02X:%02X:%02X:%02X:%02X:%02X\","
            "\"battery\":%d,\"rssi\":%d,\"hops\":%d}",
            peers[i].name,
            peers[i].mac[0], peers[i].mac[1], peers[i].mac[2],
            peers[i].mac[3], peers[i].mac[4], peers[i].mac[5],
            peers[i].battery_pct, peers[i].rssi, peers[i].hops);
        first = false;
    }
    snprintf(buf + pos, buflen - pos, "]");
}
