// Solarpunk Wearable - Auto Discovery
// Peers find each other automatically via ESP-NOW beacons.
// No configuration needed -- just power on near each other.

#include "discovery.h"
#include "mesh.h"
#include "protocol.h"
#include "../config.h"

#include "esp_log.h"

static const char* TAG = "discovery";

void discovery_init() {
    // Discovery is handled by mesh beacon broadcasts in mesh.cpp
    // This module exists for future extensions:
    // - Multi-hop routing table maintenance
    // - Network topology mapping
    // - Peer capability negotiation
    ESP_LOGI(TAG, "Auto-discovery enabled (beacon every %dms)", SP_MESH_BEACON_MS);
}
