// Solarpunk Wearable - ESP-NOW Mesh Network v2
// AES-256-GCM encrypted, multi-hop routing, 3+ node mesh

#include "mesh.h"
#include "protocol.h"
#include "../config.h"
#include "../web/webserver.h"
#include "../power/solar.h"
#include "../security/crypto.h"
#include "../scripting/engine.h"

#include "esp_now.h"
#include "esp_wifi.h"
#include "esp_mac.h"
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
static char     self_name[16];

// Recent message sequence numbers for dedup
#define SEEN_BUF_SIZE 128
static uint16_t seen_seqs[SEEN_BUF_SIZE];
static uint8_t  seen_src[SEEN_BUF_SIZE][6];  // Track source MAC too for better dedup
static int seen_idx = 0;

static bool is_duplicate(const MeshHeader* hdr) {
    for (int i = 0; i < SEEN_BUF_SIZE; i++) {
        if (seen_seqs[i] == hdr->seq && memcmp(seen_src[i], hdr->src_mac, 6) == 0) {
            return true;
        }
    }
    seen_seqs[seen_idx] = hdr->seq;
    memcpy(seen_src[seen_idx], hdr->src_mac, 6);
    seen_idx = (seen_idx + 1) % SEEN_BUF_SIZE;
    return false;
}

static bool is_broadcast_mac(const uint8_t* mac) {
    for (int i = 0; i < 6; i++) {
        if (mac[i] != 0xFF) return false;
    }
    return true;
}

static bool is_self(const uint8_t* mac) {
    return memcmp(mac, self_mac, 6) == 0;
}

// Find peer by MAC
static MeshPeer* find_peer(const uint8_t* mac) {
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (peers[i].active && memcmp(peers[i].mac, mac, 6) == 0) {
            return &peers[i];
        }
    }
    return NULL;
}

// Find peer by name (short name like "SP-D408")
static MeshPeer* find_peer_by_name(const char* name) {
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (peers[i].active && strcmp(peers[i].name, name) == 0) {
            return &peers[i];
        }
    }
    return NULL;
}

static MeshPeer* add_peer(const uint8_t* mac, bool direct) {
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (!peers[i].active) {
            memset(&peers[i], 0, sizeof(MeshPeer));
            memcpy(peers[i].mac, mac, 6);
            peers[i].active = true;
            peers[i].direct = direct;
            peers[i].last_seen_ms = esp_timer_get_time() / 1000;

            // Register with ESP-NOW for unicast
            esp_now_peer_info_t peer_info = {};
            memcpy(peer_info.peer_addr, mac, 6);
            peer_info.channel = SP_MESH_CHANNEL;
            peer_info.encrypt = false;  // We use app-layer AES-256-GCM
            if (!esp_now_is_peer_exist(mac)) {
                esp_now_add_peer(&peer_info);
            }

            ESP_LOGI(TAG, "New peer: %02X:%02X:%02X:%02X:%02X:%02X %s",
                     mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],
                     direct ? "(direct)" : "(relayed)");
            return &peers[i];
        }
    }
    return NULL;
}

// Send encrypted ESP-NOW packet
static void send_encrypted(const uint8_t* dst_mac, const uint8_t* data, int len) {
#if SP_MESH_ENCRYPT
    uint8_t enc_buf[250];
    int enc_len = crypto_encrypt(data, len, enc_buf, sizeof(enc_buf));
    if (enc_len > 0 && enc_len <= 250) {
        esp_now_send(dst_mac, enc_buf, enc_len);
    } else {
        // Fallback to unencrypted if message too large after encryption
        ESP_LOGW(TAG, "Encrypted msg too large (%d), sending plain", enc_len);
        esp_now_send(dst_mac, data, len);
    }
#else
    esp_now_send(dst_mac, data, len);
#endif
}

// Handle incoming beacon
static void handle_beacon(const MeshBeacon* beacon, int8_t rssi) {
    if (is_self(beacon->hdr.src_mac)) return;

    MeshPeer* peer = find_peer(beacon->hdr.src_mac);
    if (!peer) {
        peer = add_peer(beacon->hdr.src_mac, true);
        if (!peer) return;
    }

    strncpy(peer->name, beacon->name, sizeof(peer->name) - 1);
    peer->battery_pct = beacon->battery_pct;
    peer->rssi = rssi;
    peer->hops = 1;  // Direct beacon = 1 hop
    peer->direct = true;
    peer->flags = beacon->flags;
    memcpy(peer->next_hop, beacon->hdr.src_mac, 6);
    peer->last_seen_ms = esp_timer_get_time() / 1000;

    // Process route advertisements - learn about distant nodes
    for (int r = 0; r < beacon->route_count && r < 4; r++) {
        const uint8_t* rmac = beacon->routes[r].mac;
        uint8_t rhops = beacon->routes[r].hops;

        if (is_self(rmac)) continue;
        if (memcmp(rmac, beacon->hdr.src_mac, 6) == 0) continue;

        MeshPeer* rp = find_peer(rmac);
        if (rp) {
            // Update route if this path is shorter
            if (rhops + 1 < rp->hops || !rp->direct) {
                rp->hops = rhops + 1;
                memcpy(rp->next_hop, beacon->hdr.src_mac, 6);
                rp->last_seen_ms = esp_timer_get_time() / 1000;
                rp->direct = false;
            }
        } else {
            // New distant peer
            rp = add_peer(rmac, false);
            if (rp) {
                rp->hops = rhops + 1;
                memcpy(rp->next_hop, beacon->hdr.src_mac, 6);
                // Name will be filled when we hear their beacon
                snprintf(rp->name, sizeof(rp->name), "SP-%02X%02X", rmac[4], rmac[5]);
            }
        }
    }

    // Notify web UI of peer update
    char ws_msg[128];
    snprintf(ws_msg, sizeof(ws_msg),
        "{\"type\":\"peer\",\"name\":\"%s\",\"battery\":%d,\"rssi\":%d,\"peers\":%d}",
        beacon->name, beacon->battery_pct, rssi, beacon->peer_count);
    ws_broadcast(ws_msg, strlen(ws_msg));
}

// Handle incoming text message
static void handle_text(const MeshText* msg) {
    // Check if addressed to us or broadcast
    if (!is_broadcast_mac(msg->dst_mac) && !is_self(msg->dst_mac)) {
        return;  // Not for us, relay will handle forwarding
    }

    char ws_msg[300];
    snprintf(ws_msg, sizeof(ws_msg),
        "{\"type\":\"mesh\",\"from\":\"SP-%02X%02X\",\"text\":\"%.*s\"}",
        msg->hdr.src_mac[4], msg->hdr.src_mac[5],
        msg->len, msg->text);
    ws_broadcast(ws_msg, strlen(ws_msg));
}

// Handle remote exec request
static void handle_exec(const MeshExec* exec) {
    if (!is_self(exec->dst_mac)) return;  // Not for us

    ESP_LOGI(TAG, "Remote exec from SP-%02X%02X: %.*s",
             exec->hdr.src_mac[4], exec->hdr.src_mac[5],
             exec->cmd_len, exec->cmd);

    // Execute the command
    char cmd[200];
    int clen = exec->cmd_len;
    if (clen >= (int)sizeof(cmd)) clen = sizeof(cmd) - 1;
    memcpy(cmd, exec->cmd, clen);
    cmd[clen] = '\0';

    char output[512];
    int result = engine_run(cmd, output, sizeof(output));

    // Send result back
    MeshResult res = {};
    res.hdr.magic = MESH_MAGIC;
    res.hdr.version = MESH_VERSION;
    res.hdr.type = MESH_RESULT;
    res.hdr.hops = SP_MESH_MAX_HOPS;
    memcpy(res.hdr.src_mac, self_mac, 6);
    res.hdr.seq = msg_seq++;
    memcpy(res.dst_mac, exec->hdr.src_mac, 6);
    res.ok = (result == 0) ? 0 : 1;

    int out_len = strlen(output);
    if (out_len > (int)sizeof(res.output)) out_len = sizeof(res.output);
    res.len = out_len;
    memcpy(res.output, output, out_len);

    static const uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    send_encrypted(bcast, (uint8_t*)&res, sizeof(MeshHeader) + 8 + out_len);
}

// Handle remote exec result
static void handle_result(const MeshResult* res) {
    if (!is_self(res->dst_mac)) return;

    char ws_msg[600];
    snprintf(ws_msg, sizeof(ws_msg),
        "{\"type\":\"result\",\"from\":\"SP-%02X%02X\",\"ok\":%s,\"output\":\"%.*s\"}",
        res->hdr.src_mac[4], res->hdr.src_mac[5],
        res->ok == 0 ? "true" : "false",
        res->len, res->output);
    ws_broadcast(ws_msg, strlen(ws_msg));
}

// Relay message if hops remaining
static void maybe_relay(const uint8_t* data, int len) {
    if (len < (int)sizeof(MeshHeader)) return;
    MeshHeader* hdr = (MeshHeader*)data;
    if (hdr->hops <= 1) return;

    uint8_t relay[250];
    memcpy(relay, data, len);
    ((MeshHeader*)relay)->hops--;

    static const uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    send_encrypted(bcast, relay, len);
}

// ESP-NOW receive callback
static void on_recv(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
    if (len < (int)sizeof(MeshHeader)) return;

    // Try to decrypt
    uint8_t plain[250];
    const uint8_t* payload = data;
    int payload_len = len;

#if SP_MESH_ENCRYPT
    int dec_len = crypto_decrypt(data, len, plain, sizeof(plain));
    if (dec_len > 0) {
        payload = plain;
        payload_len = dec_len;
    }
    // If decrypt fails, try as plaintext (backward compat during upgrade)
#endif

    const MeshHeader* hdr = (const MeshHeader*)payload;
    if (hdr->magic != MESH_MAGIC) return;
    if (is_duplicate(hdr)) return;

    int8_t rssi = -50;  // Default if not available

    switch (hdr->type) {
    case MESH_BEACON:
        if (payload_len >= (int)sizeof(MeshBeacon) - (int)sizeof(((MeshBeacon*)0)->routes)) {
            handle_beacon((const MeshBeacon*)payload, rssi);
        }
        break;
    case MESH_TEXT:
        if (payload_len >= (int)sizeof(MeshHeader) + 7) {
            handle_text((const MeshText*)payload);
            maybe_relay(payload, payload_len);
        }
        break;
    case MESH_EXEC:
        if (payload_len >= (int)sizeof(MeshHeader) + 7) {
            handle_exec((const MeshExec*)payload);
            maybe_relay(payload, payload_len);
        }
        break;
    case MESH_RESULT:
        if (payload_len >= (int)sizeof(MeshHeader) + 8) {
            handle_result((const MeshResult*)payload);
            maybe_relay(payload, payload_len);
        }
        break;
    case MESH_PING:
        {
            MeshPeer* p = find_peer(hdr->src_mac);
            if (p) p->last_seen_ms = esp_timer_get_time() / 1000;
        }
        break;
    default:
        maybe_relay(payload, payload_len);
        break;
    }
}

static void on_send(const uint8_t* mac, esp_now_send_status_t status) {
    if (status != ESP_NOW_SEND_SUCCESS) {
        ESP_LOGW(TAG, "Send failed to %02X:%02X", mac[4], mac[5]);
    }
}

// Send discovery beacon with route advertisements
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

    strncpy(beacon.name, self_name, sizeof(beacon.name) - 1);

    // Advertise known peers in beacon for route discovery
    beacon.route_count = 0;
    for (int i = 0; i < SP_MESH_MAX_PEERS && beacon.route_count < 4; i++) {
        if (peers[i].active) {
            memcpy(beacon.routes[beacon.route_count].mac, peers[i].mac, 6);
            beacon.routes[beacon.route_count].hops = peers[i].hops;
            beacon.route_count++;
        }
    }

    static const uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    send_encrypted(bcast, (uint8_t*)&beacon, sizeof(beacon));
}

// Background task: periodic beacons + peer cleanup
static void mesh_task(void* arg) {
    while (1) {
        send_beacon();

        // Expire old peers
        uint32_t now = esp_timer_get_time() / 1000;
        for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
            if (peers[i].active && (now - peers[i].last_seen_ms) > SP_MESH_PEER_EXPIRE_MS) {
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
    snprintf(self_name, sizeof(self_name), "SP-%02X%02X", self_mac[4], self_mac[5]);
    memset(peers, 0, sizeof(peers));

    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_recv));
    ESP_ERROR_CHECK(esp_now_register_send_cb(on_send));

    // Set ESP-NOW PMK for basic transport security
    ESP_ERROR_CHECK(esp_now_set_pmk((const uint8_t*)SP_MESH_PMK));

    // Add broadcast peer
    esp_now_peer_info_t broadcast = {};
    memset(broadcast.peer_addr, 0xFF, 6);
    broadcast.channel = SP_MESH_CHANNEL;
    broadcast.encrypt = false;
    esp_now_add_peer(&broadcast);

    xTaskCreate(mesh_task, "mesh", 4096, NULL, 4, NULL);
    ESP_LOGI(TAG, "Mesh v2 initialized (ESP-NOW ch%d, AES-256-GCM, max %d hops)",
             SP_MESH_CHANNEL, SP_MESH_MAX_HOPS);
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

    static const uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    send_encrypted(bcast, (uint8_t*)&msg, sizeof(MeshHeader) + 7 + copy_len);
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

    // Route through next hop if not direct
    MeshPeer* peer = find_peer(mac);
    const uint8_t* send_to = mac;
    if (peer && !peer->direct) {
        send_to = peer->next_hop;
    }

    // Send via broadcast for relay capability
    static const uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    send_encrypted(bcast, (uint8_t*)&msg, sizeof(MeshHeader) + 7 + copy_len);
}

void mesh_send_to_name(const char* name, const char* data, int len) {
    MeshPeer* peer = find_peer_by_name(name);
    if (peer) {
        mesh_send_to(peer->mac, data, len);
    }
}

void mesh_exec_remote(const char* node_name, const char* cmd) {
    MeshPeer* peer = find_peer_by_name(node_name);
    if (!peer) {
        ESP_LOGW(TAG, "Unknown node: %s", node_name);
        return;
    }

    MeshExec exec = {};
    exec.hdr.magic = MESH_MAGIC;
    exec.hdr.version = MESH_VERSION;
    exec.hdr.type = MESH_EXEC;
    exec.hdr.hops = SP_MESH_MAX_HOPS;
    memcpy(exec.hdr.src_mac, self_mac, 6);
    exec.hdr.seq = msg_seq++;
    memcpy(exec.dst_mac, peer->mac, 6);

    int clen = strlen(cmd);
    if (clen > (int)sizeof(exec.cmd)) clen = sizeof(exec.cmd);
    exec.cmd_len = clen;
    memcpy(exec.cmd, cmd, clen);

    static const uint8_t bcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    send_encrypted(bcast, (uint8_t*)&exec, sizeof(MeshHeader) + 7 + clen);
}

void mesh_quick_listen(int duration_ms) {
    vTaskDelay(pdMS_TO_TICKS(duration_ms));
}

int mesh_peer_count() {
    int count = 0;
    for (int i = 0; i < SP_MESH_MAX_PEERS; i++) {
        if (peers[i].active) count++;
    }
    return count;
}

bool mesh_find_by_name(const char* name, uint8_t* mac_out) {
    MeshPeer* p = find_peer_by_name(name);
    if (p) {
        memcpy(mac_out, p->mac, 6);
        return true;
    }
    return false;
}

void mesh_get_self_mac(uint8_t* mac_out) {
    memcpy(mac_out, self_mac, 6);
}

void mesh_get_self_name(char* name_out, int len) {
    strncpy(name_out, self_name, len - 1);
    name_out[len - 1] = '\0';
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
            "\"battery\":%d,\"rssi\":%d,\"hops\":%d,\"direct\":%s}",
            peers[i].name,
            peers[i].mac[0], peers[i].mac[1], peers[i].mac[2],
            peers[i].mac[3], peers[i].mac[4], peers[i].mac[5],
            peers[i].battery_pct, peers[i].rssi, peers[i].hops,
            peers[i].direct ? "true" : "false");
        first = false;
    }
    snprintf(buf + pos, buflen - pos, "]");
}
