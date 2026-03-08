// Solarpunk Wearable - Web Server
// HTTP server for the IDE + WebSocket for live terminal

#include "webserver.h"
#include "../config.h"
#include "../scripting/engine.h"
#include "../mesh/mesh.h"
#include "../power/solar.h"

#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"
#include <cstring>
#include <cstdio>
#include <cstdlib>

static const char* TAG = "webserver";
static httpd_handle_t server = NULL;

// Embedded static files (linked by CMake EMBED_FILES)
extern const uint8_t index_html_start[] asm("_binary_index_html_start");
extern const uint8_t index_html_end[]   asm("_binary_index_html_end");
extern const uint8_t style_css_start[]  asm("_binary_style_css_start");
extern const uint8_t style_css_end[]    asm("_binary_style_css_end");
extern const uint8_t app_js_start[]     asm("_binary_app_js_start");
extern const uint8_t app_js_end[]       asm("_binary_app_js_end");

// WebSocket file descriptors for connected clients
static int ws_fds[SP_MAX_WS_CLIENTS] = {0};

// --- Static file handlers ---

static esp_err_t index_handler(httpd_req_t* req) {
    httpd_resp_set_type(req, "text/html");
    httpd_resp_send(req, (const char*)index_html_start,
                    index_html_end - index_html_start);
    return ESP_OK;
}

static esp_err_t css_handler(httpd_req_t* req) {
    httpd_resp_set_type(req, "text/css");
    httpd_resp_send(req, (const char*)style_css_start,
                    style_css_end - style_css_start);
    return ESP_OK;
}

static esp_err_t js_handler(httpd_req_t* req) {
    httpd_resp_set_type(req, "application/javascript");
    httpd_resp_send(req, (const char*)app_js_start,
                    app_js_end - app_js_start);
    return ESP_OK;
}

// --- API handlers ---

// GET /api/status - device status JSON
static esp_err_t status_handler(httpd_req_t* req) {
    char buf[256];
    int battery = solar_battery_percent();
    int solar_mv = solar_panel_mv();
    int peers = mesh_peer_count();

    snprintf(buf, sizeof(buf),
        "{\"battery\":%d,\"solar_mv\":%d,\"peers\":%d,"
        "\"free_heap\":%lu,\"uptime\":%lld,\"version\":\"%s\"}",
        battery, solar_mv, peers,
        (unsigned long)esp_get_free_heap_size(),
        esp_timer_get_time() / 1000000LL,
        SP_FIRMWARE_VERSION);

    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, buf, strlen(buf));
    return ESP_OK;
}

// POST /api/run - execute a script
static esp_err_t run_handler(httpd_req_t* req) {
    if (req->content_len > SP_MAX_SCRIPT_SIZE) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Script too large");
        return ESP_FAIL;
    }

    char* script = (char*)malloc(req->content_len + 1);
    if (!script) {
        httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR, "Out of memory");
        return ESP_FAIL;
    }

    int received = httpd_req_recv(req, script, req->content_len);
    if (received <= 0) {
        free(script);
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Failed to read body");
        return ESP_FAIL;
    }
    script[received] = '\0';

    // Run script and capture output
    char output[1024];
    int result = engine_run(script, output, sizeof(output));
    free(script);

    httpd_resp_set_type(req, "application/json");
    char resp[1200];
    snprintf(resp, sizeof(resp), "{\"ok\":%s,\"output\":\"%s\"}",
             result == 0 ? "true" : "false", output);
    httpd_resp_send(req, resp, strlen(resp));
    return ESP_OK;
}

// POST /api/mesh/send - send message to mesh
static esp_err_t mesh_send_handler(httpd_req_t* req) {
    char buf[SP_MESH_MSG_SIZE];
    int len = httpd_req_recv(req, buf, sizeof(buf) - 1);
    if (len <= 0) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "No data");
        return ESP_FAIL;
    }
    buf[len] = '\0';

    mesh_broadcast(buf, len);

    httpd_resp_set_type(req, "application/json");
    httpd_resp_sendstr(req, "{\"ok\":true}");
    return ESP_OK;
}

// GET /api/mesh/peers - list discovered peers
static esp_err_t mesh_peers_handler(httpd_req_t* req) {
    char buf[1024];
    mesh_peers_json(buf, sizeof(buf));
    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, buf, strlen(buf));
    return ESP_OK;
}

// --- WebSocket handler ---

static esp_err_t ws_handler(httpd_req_t* req) {
    if (req->method == HTTP_GET) {
        // New WebSocket connection
        ESP_LOGI(TAG, "WS client connected");
        // Store FD for broadcasting
        for (int i = 0; i < SP_MAX_WS_CLIENTS; i++) {
            if (ws_fds[i] == 0) {
                ws_fds[i] = httpd_req_to_sockfd(req);
                break;
            }
        }
        return ESP_OK;
    }

    // Receive WebSocket frame
    httpd_ws_frame_t ws_pkt;
    memset(&ws_pkt, 0, sizeof(ws_pkt));
    ws_pkt.type = HTTPD_WS_TYPE_TEXT;

    esp_err_t ret = httpd_ws_recv_frame(req, &ws_pkt, 0);
    if (ret != ESP_OK) return ret;

    if (ws_pkt.len > 0) {
        uint8_t* buf = (uint8_t*)malloc(ws_pkt.len + 1);
        if (!buf) return ESP_ERR_NO_MEM;

        ws_pkt.payload = buf;
        ret = httpd_ws_recv_frame(req, &ws_pkt, ws_pkt.len);
        if (ret == ESP_OK) {
            buf[ws_pkt.len] = '\0';
            // Execute as command in script engine
            char output[512];
            engine_run((const char*)buf, output, sizeof(output));

            // Send response back
            httpd_ws_frame_t ws_resp = {};
            ws_resp.type = HTTPD_WS_TYPE_TEXT;
            ws_resp.payload = (uint8_t*)output;
            ws_resp.len = strlen(output);
            httpd_ws_send_frame(req, &ws_resp);
        }
        free(buf);
    }
    return ESP_OK;
}

// Broadcast message to all WebSocket clients
void ws_broadcast(const char* msg, int len) {
    httpd_ws_frame_t frame = {};
    frame.type = HTTPD_WS_TYPE_TEXT;
    frame.payload = (uint8_t*)msg;
    frame.len = len;

    for (int i = 0; i < SP_MAX_WS_CLIENTS; i++) {
        if (ws_fds[i] != 0) {
            if (httpd_ws_send_frame_async(server, ws_fds[i], &frame) != ESP_OK) {
                ws_fds[i] = 0;  // Client gone
            }
        }
    }
}

int ws_client_count() {
    int count = 0;
    for (int i = 0; i < SP_MAX_WS_CLIENTS; i++) {
        if (ws_fds[i] != 0) count++;
    }
    return count;
}

// --- Server init ---

void webserver_init() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_uri_handlers = 10;
    config.uri_match_fn = httpd_uri_match_wildcard;
    config.lru_purge_enable = true;

    if (httpd_start(&server, &config) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start HTTP server");
        return;
    }

    // Helper to register URI handlers
    auto reg = [&](const char* uri, httpd_method_t method, esp_err_t (*handler)(httpd_req_t*), bool websocket = false) {
        httpd_uri_t u = {};
        u.uri = uri;
        u.method = method;
        u.handler = handler;
        u.is_websocket = websocket;
        httpd_register_uri_handler(server, &u);
    };

    // Static files
    reg("/",          HTTP_GET, index_handler);
    reg("/style.css", HTTP_GET, css_handler);
    reg("/app.js",    HTTP_GET, js_handler);

    // API endpoints
    reg("/api/status",     HTTP_GET,  status_handler);
    reg("/api/run",        HTTP_POST, run_handler);
    reg("/api/mesh/send",  HTTP_POST, mesh_send_handler);
    reg("/api/mesh/peers", HTTP_GET,  mesh_peers_handler);

    // WebSocket (terminal)
    reg("/ws", HTTP_GET, ws_handler, true);


    ESP_LOGI(TAG, "Web IDE server started on port %d", config.server_port);
}

void webserver_stop() {
    if (server) {
        httpd_stop(server);
        server = NULL;
    }
}
