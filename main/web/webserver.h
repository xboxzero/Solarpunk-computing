#pragma once

// HTTP + WebSocket server for the web IDE
// Serves the editor UI and handles terminal I/O over WebSocket

void webserver_init();
void webserver_stop();
void ws_broadcast(const char* msg, int len);
int  ws_client_count();
