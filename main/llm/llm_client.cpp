// Solarpunk Wearable - LLM Client + Agent System
// Agent can execute device commands, read sensors, write scripts, analyze data

#include "llm_client.h"
#include "../config.h"
#include "../web/webserver.h"
#include "../scripting/engine.h"
#include "../mesh/mesh.h"
#include "../power/solar.h"

#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"
#include <cstring>
#include <cstdio>

static const char* TAG = "llm";
static bool connected = false;

typedef struct {
    char* buf;
    int   size;
    int   pos;
} resp_buf_t;

static esp_err_t http_event_handler(esp_http_client_event_t* evt) {
    resp_buf_t* rb = (resp_buf_t*)evt->user_data;
    if (evt->event_id == HTTP_EVENT_ON_DATA && rb) {
        int copy = evt->data_len;
        if (rb->pos + copy >= rb->size) {
            copy = rb->size - rb->pos - 1;
        }
        if (copy > 0) {
            memcpy(rb->buf + rb->pos, evt->data, copy);
            rb->pos += copy;
            rb->buf[rb->pos] = '\0';
        }
    }
    return ESP_OK;
}

void llm_init() {
    ESP_LOGI(TAG, "LLM agent ready (server: %s:%d)", SP_LLM_HOST, SP_LLM_PORT);
}

// Simple JSON string value extractor
static void extract_json_string(const char* json, const char* key, char* out, int out_size) {
    out[0] = '\0';
    char search[64];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char* pos = strstr(json, search);
    if (!pos) return;

    pos = strchr(pos + strlen(search), ':');
    if (!pos) return;
    pos++;
    while (*pos == ' ' || *pos == '\t') pos++;

    if (*pos == '"') {
        pos++;
        int i = 0;
        while (*pos && *pos != '"' && i < out_size - 1) {
            if (*pos == '\\' && *(pos + 1)) {
                pos++;
                switch (*pos) {
                    case 'n': out[i++] = '\n'; break;
                    case 't': out[i++] = '\t'; break;
                    case '"': out[i++] = '"'; break;
                    case '\\': out[i++] = '\\'; break;
                    default: out[i++] = *pos; break;
                }
            } else {
                out[i++] = *pos;
            }
            pos++;
        }
        out[i] = '\0';
    }
}

// Escape string for JSON
static int json_escape(const char* in, char* out, int out_size) {
    int ei = 0;
    for (int i = 0; in[i] && ei < out_size - 2; i++) {
        if (in[i] == '"' || in[i] == '\\') {
            out[ei++] = '\\';
        } else if (in[i] == '\n') {
            out[ei++] = '\\';
            out[ei++] = 'n';
            continue;
        } else if (in[i] == '\r') {
            continue;
        } else if (in[i] == '\t') {
            out[ei++] = '\\';
            out[ei++] = 't';
            continue;
        }
        out[ei++] = in[i];
    }
    out[ei] = '\0';
    return ei;
}

// Raw LLM completion call
static int llm_complete(const char* prompt, char* response, int response_size) {
    if (!prompt || !response || response_size < 2) return -1;
    response[0] = '\0';

    char escaped[1024];
    json_escape(prompt, escaped, sizeof(escaped));

    char body[1536];
    snprintf(body, sizeof(body),
        "{\"prompt\":\"%s\","
        "\"n_predict\":%d,"
        "\"temperature\":0.4,"
        "\"stop\":[\"\\n\\n\\n\",\"DONE:\"],"
        "\"repeat_penalty\":1.1"
        "}",
        escaped, SP_LLM_MAX_TOKENS);

    char url[128];
    snprintf(url, sizeof(url), "http://%s:%d/completion", SP_LLM_HOST, SP_LLM_PORT);

    char http_buf[4096];
    resp_buf_t rb = { .buf = http_buf, .size = sizeof(http_buf), .pos = 0 };

    esp_http_client_config_t config = {};
    config.url = url;
    config.method = HTTP_METHOD_POST;
    config.timeout_ms = SP_LLM_TIMEOUT_MS;
    config.event_handler = http_event_handler;
    config.user_data = &rb;
    config.disable_auto_redirect = true;

    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) {
        snprintf(response, response_size, "[error] failed to create HTTP client");
        connected = false;
        return -1;
    }

    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_post_field(client, body, strlen(body));

    esp_err_t err = esp_http_client_perform(client);
    int status = esp_http_client_get_status_code(client);
    esp_http_client_cleanup(client);

    if (err != ESP_OK) {
        snprintf(response, response_size, "[error] cannot reach LLM at %s:%d", SP_LLM_HOST, SP_LLM_PORT);
        connected = false;
        return -1;
    }

    if (status != 200) {
        snprintf(response, response_size, "[error] LLM returned %d", status);
        connected = false;
        return -1;
    }

    connected = true;
    extract_json_string(http_buf, "content", response, response_size);

    if (response[0] == '\0') {
        snprintf(response, response_size, "[error] empty LLM response");
        return -1;
    }

    // Trim leading whitespace
    char* start = response;
    while (*start == ' ' || *start == '\n') start++;
    if (start != response) {
        memmove(response, start, strlen(start) + 1);
    }

    return 0;
}

int llm_ask(const char* prompt, char* response, int response_size) {
    char full_prompt[1024];
    snprintf(full_prompt, sizeof(full_prompt), "Q: %s\nA:", prompt);
    return llm_complete(full_prompt, response, response_size);
}

// Broadcast agent progress to WebSocket
static void agent_ws(const char* cls, const char* text) {
    char escaped[512];
    json_escape(text, escaped, sizeof(escaped));
    char msg[600];
    snprintf(msg, sizeof(msg), "{\"type\":\"agent\",\"cls\":\"%s\",\"text\":\"%s\"}", cls, escaped);
    ws_broadcast(msg, strlen(msg));
}

// Build system context for agent
static void build_context(char* buf, int buflen) {
    char node_name[16];
    mesh_get_self_name(node_name, sizeof(node_name));

    int pos = 0;
    pos += snprintf(buf + pos, buflen - pos,
        "You are an AI agent on a Solarpunk ESP32 wearable.\n"
        "Node: %s | Bat: %d%% | Solar: %dmV | Heap: %lu | Peers: %d\n"
        "Commands: status, peers, send <msg>, send @<node> <msg>, "
        "exec @<node> <cmd>, gpio <p> <v>, read <p>, adc <p>, "
        "write <file> <content>, cat <file>, ls, free, uptime\n"
        "Reply with CMD: <command> lines. End with DONE: <summary>.\n",
        node_name, solar_battery_percent(), solar_panel_mv(),
        (unsigned long)esp_get_free_heap_size(), mesh_peer_count());

    // Append truncated peers info if room
    if (pos < buflen - 64) {
        char peers_json[256];
        mesh_peers_json(peers_json, sizeof(peers_json));
        pos += snprintf(buf + pos, buflen - pos, "Peers: %.200s\n", peers_json);
    }
}

// Parse and execute CMD: lines from LLM response
// Returns number of commands executed
static int parse_and_exec(const char* response, char* results, int results_size) {
    int rpos = 0;
    int cmd_count = 0;
    const char* p = response;

    while (*p && cmd_count < SP_AGENT_MAX_CMDS) {
        // Find "CMD:" prefix
        const char* cmd_start = strstr(p, "CMD:");
        if (!cmd_start) break;

        cmd_start += 4;
        while (*cmd_start == ' ') cmd_start++;

        // Find end of line
        const char* cmd_end = cmd_start;
        while (*cmd_end && *cmd_end != '\n') cmd_end++;

        int cmd_len = cmd_end - cmd_start;
        if (cmd_len > 0 && cmd_len < 256) {
            char cmd[256];
            memcpy(cmd, cmd_start, cmd_len);
            cmd[cmd_len] = '\0';

            // Trim trailing whitespace
            while (cmd_len > 0 && (cmd[cmd_len-1] == ' ' || cmd[cmd_len-1] == '\r')) {
                cmd[--cmd_len] = '\0';
            }

            agent_ws("agent-cmd", cmd);

            char output[512];
            engine_run(cmd, output, sizeof(output));

            agent_ws("agent-out", output);

            rpos += snprintf(results + rpos, results_size - rpos,
                "$ %s\n%s\n", cmd, output);
            cmd_count++;
        }

        p = cmd_end;
        if (*p) p++;
    }

    return cmd_count;
}

int llm_agent(const char* task, char* summary, int summary_size) {
    if (!task || !summary || summary_size < 2) return -1;
    summary[0] = '\0';

    agent_ws("agent-start", task);

    char context[1024];
    build_context(context, sizeof(context));

    // Build initial prompt
    char prompt[3072];
    snprintf(prompt, sizeof(prompt), "%s\nTask: %s\n", context, task);

    char response[2048];
    char results[1024];

    for (int iter = 0; iter < SP_AGENT_MAX_ITERS; iter++) {
        agent_ws("agent-think", "thinking...");

        if (llm_complete(prompt, response, sizeof(response)) != 0) {
            snprintf(summary, summary_size, "[error] LLM unreachable");
            agent_ws("agent-err", "LLM unreachable");
            return -1;
        }

        // Check for DONE:
        const char* done = strstr(response, "DONE:");
        if (done) {
            done += 5;
            while (*done == ' ') done++;
            strncpy(summary, done, summary_size - 1);
            summary[summary_size - 1] = '\0';

            // Still execute any CMD: lines before DONE:
            results[0] = '\0';
            parse_and_exec(response, results, sizeof(results));

            agent_ws("agent-done", summary);
            return 0;
        }

        // Execute commands
        results[0] = '\0';
        int ncmds = parse_and_exec(response, results, sizeof(results));

        if (ncmds == 0) {
            // No commands and no DONE - treat response as the summary
            strncpy(summary, response, summary_size - 1);
            summary[summary_size - 1] = '\0';
            agent_ws("agent-done", summary);
            return 0;
        }

        // Build follow-up prompt with results (truncate results to fit)
        snprintf(prompt, sizeof(prompt),
            "%s\nTask: %s\n\nPrevious results:\n%.800s\n"
            "Continue. CMD: for commands, DONE: to finish.\n",
            context, task, results);
    }

    snprintf(summary, summary_size, "Agent reached max iterations (%d)", SP_AGENT_MAX_ITERS);
    agent_ws("agent-done", summary);
    return 0;
}

bool llm_is_connected() {
    return connected;
}
