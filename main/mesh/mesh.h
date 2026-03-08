#pragma once

#include <cstdint>

// ESP-NOW mesh networking layer
// AES-256-GCM encrypted, multi-hop routing, 3+ node support

void mesh_init();
void mesh_broadcast(const char* data, int len);
void mesh_send_to(const uint8_t* mac, const char* data, int len);
void mesh_send_to_name(const char* name, const char* data, int len);
void mesh_exec_remote(const char* node_name, const char* cmd);
void mesh_quick_listen(int duration_ms);
int  mesh_peer_count();
void mesh_peers_json(char* buf, int buflen);
bool mesh_find_by_name(const char* name, uint8_t* mac_out);
void mesh_get_self_mac(uint8_t* mac_out);
void mesh_get_self_name(char* name_out, int len);
