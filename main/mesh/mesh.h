#pragma once

// ESP-NOW mesh networking layer
// Handles send/receive, relay, peer tracking

void mesh_init();
void mesh_broadcast(const char* data, int len);
void mesh_send_to(const uint8_t* mac, const char* data, int len);
void mesh_quick_listen(int duration_ms);
int  mesh_peer_count();
void mesh_peers_json(char* buf, int buflen);
