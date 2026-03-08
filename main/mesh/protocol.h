#pragma once

#include <cstdint>

// ============================================================
// Solarpunk Mesh Protocol
// ESP-NOW based, 250 byte max payload
// ============================================================

// Message types
enum MeshMsgType : uint8_t {
    MESH_BEACON     = 0x01,  // Discovery beacon (broadcast)
    MESH_TEXT       = 0x02,  // Text message (chat)
    MESH_FILE       = 0x03,  // File transfer chunk
    MESH_SCRIPT     = 0x04,  // Deploy script to peer
    MESH_SENSOR     = 0x05,  // Sensor data relay
    MESH_ACK        = 0x06,  // Acknowledgement
    MESH_PING       = 0x07,  // Keepalive
    MESH_SLEEP_SYNC = 0x08,  // Coordinated sleep schedule
};

// Common header for all mesh messages (12 bytes)
struct __attribute__((packed)) MeshHeader {
    uint8_t  magic;       // 0xSP (0x53)
    uint8_t  version;     // Protocol version (1)
    uint8_t  type;        // MeshMsgType
    uint8_t  hops;        // Hop count (decremented at each relay)
    uint8_t  src_mac[6];  // Original sender MAC
    uint16_t seq;         // Sequence number (dedup)
};

// Beacon payload (broadcast for discovery)
struct __attribute__((packed)) MeshBeacon {
    MeshHeader hdr;
    uint8_t  battery_pct;   // Battery level
    uint8_t  solar_active;  // 1 if solar is charging
    uint8_t  peer_count;    // Known peers
    uint8_t  flags;         // Capabilities
    char     name[16];      // Human-readable node name
};

// Text message
struct __attribute__((packed)) MeshText {
    MeshHeader hdr;
    uint8_t  dst_mac[6];    // Destination (FF:FF:FF:FF:FF:FF = broadcast)
    uint8_t  len;
    char     text[200 - sizeof(MeshHeader) - 7];
};

// Sleep sync message (coordinate wake windows)
struct __attribute__((packed)) MeshSleepSync {
    MeshHeader hdr;
    uint32_t next_wake_ms;     // Milliseconds until next wake
    uint16_t listen_window_ms; // How long to listen
    uint16_t epoch;            // Sleep schedule epoch (for agreement)
};

// Peer info (stored in neighbor table)
struct MeshPeer {
    uint8_t  mac[6];
    char     name[16];
    uint8_t  battery_pct;
    int8_t   rssi;          // Signal strength
    uint32_t last_seen_ms;  // Tick when last heard
    uint8_t  hops;          // Distance in hops
    bool     active;
};

#define MESH_MAGIC    0x53
#define MESH_VERSION  1
