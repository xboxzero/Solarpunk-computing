#include "web3.h"
#include "../kernel/kernel.h"
#include "../kernel/scheduler.h"
#include "../kernel/memory.h"
#include "../net/net.h"
#include "../drivers/uart.h"
#include "../container/container.h"

namespace solarpunk {

// Minimal Keccak-256 implementation
// Round constants
static const uint64_t keccak_rc[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL, 0x800000000000808AULL,
    0x8000000080008000ULL, 0x000000000000808BULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL, 0x000000000000008AULL,
    0x0000000000000088ULL, 0x0000000080008009ULL, 0x000000008000000AULL,
    0x000000008000808BULL, 0x800000000000008BULL, 0x8000000000008089ULL,
    0x8000000000008003ULL, 0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800AULL, 0x800000008000000AULL, 0x8000000080008081ULL,
    0x8000000000008080ULL, 0x0000000080000001ULL, 0x8000000080008008ULL,
};

static uint64_t rotl64(uint64_t x, int n) {
    return (x << n) | (x >> (64 - n));
}

static void keccak_f1600(uint64_t state[25]) {
    for (int round = 0; round < 24; round++) {
        // Theta
        uint64_t C[5], D[5];
        for (int i = 0; i < 5; i++)
            C[i] = state[i] ^ state[i+5] ^ state[i+10] ^ state[i+15] ^ state[i+20];
        for (int i = 0; i < 5; i++) {
            D[i] = C[(i+4)%5] ^ rotl64(C[(i+1)%5], 1);
            for (int j = 0; j < 25; j += 5)
                state[j+i] ^= D[i];
        }

        // Rho and Pi
        uint64_t B[25];
        static const int rho[25] = {
            0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14
        };
        static const int pi[25] = {
            0,10,20,5,15,16,1,11,21,6,7,17,2,12,22,23,8,18,3,13,14,24,9,19,4
        };
        for (int i = 0; i < 25; i++)
            B[pi[i]] = rotl64(state[i], rho[i]);

        // Chi
        for (int j = 0; j < 25; j += 5)
            for (int i = 0; i < 5; i++)
                state[j+i] = B[j+i] ^ (~B[j+(i+1)%5] & B[j+(i+2)%5]);

        // Iota
        state[0] ^= keccak_rc[round];
    }
}

void keccak256(const uint8_t* data, uint32_t len, Hash256& out) {
    uint64_t state[25] = {0};
    const uint32_t rate = 136; // (1600 - 256*2) / 8

    // Absorb
    uint32_t offset = 0;
    while (offset + rate <= len) {
        for (uint32_t i = 0; i < rate / 8; i++) {
            uint64_t lane = 0;
            for (int j = 0; j < 8; j++)
                lane |= (uint64_t)data[offset + i*8 + j] << (8*j);
            state[i] ^= lane;
        }
        keccak_f1600(state);
        offset += rate;
    }

    // Pad and final absorb
    uint8_t pad[136] = {0};
    uint32_t remaining = len - offset;
    for (uint32_t i = 0; i < remaining; i++)
        pad[i] = data[offset + i];
    pad[remaining] = 0x01;
    pad[rate - 1] |= 0x80;

    for (uint32_t i = 0; i < rate / 8; i++) {
        uint64_t lane = 0;
        for (int j = 0; j < 8; j++)
            lane |= (uint64_t)pad[i*8 + j] << (8*j);
        state[i] ^= lane;
    }
    keccak_f1600(state);

    // Squeeze
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 8; j++)
            out.bytes[i*8 + j] = (state[i] >> (8*j)) & 0xFF;
    }
}

// Simple JSON parser for RPC
struct JsonRpc {
    char method[64];
    char params[256];
    int  id;
};

static bool parse_json_rpc(const char* json, JsonRpc& rpc) {
    rpc.method[0] = 0;
    rpc.params[0] = 0;
    rpc.id = 0;

    // Find "method":"..."
    const char* m = json;
    while (*m) {
        if (m[0] == '"' && m[1] == 'm' && m[2] == 'e' && m[3] == 't') {
            m += 10; // skip "method":"
            int i = 0;
            while (*m && *m != '"' && i < 63)
                rpc.method[i++] = *m++;
            rpc.method[i] = 0;
        }
        if (m[0] == '"' && m[1] == 'i' && m[2] == 'd' && m[3] == '"') {
            m += 4;
            while (*m && (*m < '0' || *m > '9')) m++;
            rpc.id = 0;
            while (*m >= '0' && *m <= '9')
                rpc.id = rpc.id * 10 + (*m++ - '0');
        }
        m++;
    }
    return rpc.method[0] != 0;
}

RpcMethod parse_rpc_method(const char* method) {
    // String compare helper
    auto eq = [](const char* a, const char* b) -> bool {
        while (*a && *b) { if (*a++ != *b++) return false; }
        return *a == *b;
    };

    if (eq(method, "eth_blockNumber"))     return RpcMethod::ETH_BLOCK_NUMBER;
    if (eq(method, "eth_getBalance"))      return RpcMethod::ETH_GET_BALANCE;
    if (eq(method, "eth_sendTransaction")) return RpcMethod::ETH_SEND_TRANSACTION;
    if (eq(method, "eth_getBlockByNumber"))return RpcMethod::ETH_GET_BLOCK;
    if (eq(method, "eth_chainId"))         return RpcMethod::ETH_CHAIN_ID;
    if (eq(method, "net_version"))         return RpcMethod::NET_VERSION;
    if (eq(method, "web3_clientVersion"))  return RpcMethod::WEB3_CLIENT_VERSION;
    if (eq(method, "sp_systemInfo"))       return RpcMethod::SP_SYSTEM_INFO;
    if (eq(method, "sp_containerList"))    return RpcMethod::SP_CONTAINER_LIST;
    return RpcMethod::UNKNOWN;
}

// State
static Block current_block = {0, {}, {}, 0, 0};
static uint64_t chain_id = 0x534F4C41; // "SOLA" in hex

static int write_response(char* buf, int id, const char* result) {
    // Build JSON-RPC response
    char* p = buf;
    const char* prefix = "{\"jsonrpc\":\"2.0\",\"id\":";
    while (*prefix) *p++ = *prefix++;

    // Write id
    char num[12];
    int ni = 0;
    int tmp = id;
    if (tmp == 0) num[ni++] = '0';
    else { while (tmp > 0) { num[ni++] = '0' + tmp % 10; tmp /= 10; } }
    for (int i = ni - 1; i >= 0; i--) *p++ = num[i];

    const char* mid = ",\"result\":";
    while (*mid) *p++ = *mid++;
    while (*result) *p++ = *result++;
    *p++ = '}';
    *p = 0;

    return p - buf;
}

static void handle_rpc(const char* request, char* response, int& resp_len) {
    JsonRpc rpc;
    if (!parse_json_rpc(request, rpc)) {
        resp_len = write_response(response, 0, "\"parse error\"");
        return;
    }

    RpcMethod method = parse_rpc_method(rpc.method);
    char result[256];

    switch (method) {
    case RpcMethod::WEB3_CLIENT_VERSION:
        resp_len = write_response(response, rpc.id,
            "\"SolarpunkOS/0.1.0/bare-metal\"");
        break;

    case RpcMethod::ETH_CHAIN_ID: {
        // Return chain ID as hex
        char hex[20] = "\"0x";
        char* h = hex + 3;
        for (int i = 28; i >= 0; i -= 4) {
            uint8_t nib = (chain_id >> i) & 0xF;
            *h++ = nib < 10 ? '0' + nib : 'a' + nib - 10;
        }
        *h++ = '"'; *h = 0;
        resp_len = write_response(response, rpc.id, hex);
        break;
    }

    case RpcMethod::ETH_BLOCK_NUMBER: {
        char hex[20] = "\"0x";
        char* h = hex + 3;
        uint64_t bn = current_block.number;
        bool started = false;
        for (int i = 60; i >= 0; i -= 4) {
            uint8_t nib = (bn >> i) & 0xF;
            if (nib || started || i == 0) {
                *h++ = nib < 10 ? '0' + nib : 'a' + nib - 10;
                started = true;
            }
        }
        *h++ = '"'; *h = 0;
        resp_len = write_response(response, rpc.id, hex);
        break;
    }

    case RpcMethod::NET_VERSION:
        resp_len = write_response(response, rpc.id, "\"1397572929\"");
        break;

    case RpcMethod::SP_SYSTEM_INFO: {
        auto info = kernel_info();
        char r[256];
        int n = 0;
        const char* pre = "{\"platform\":\"";
        while (*pre) r[n++] = *pre++;
        const char* pl = info.platform;
        while (*pl) r[n++] = *pl++;
        const char* mid2 = "\",\"uptime_ms\":";
        while (*mid2) r[n++] = *mid2++;
        // Write uptime number
        char num2[12]; int ni2 = 0;
        uint32_t u = info.uptime_ms;
        if (u == 0) num2[ni2++] = '0';
        else { while (u > 0) { num2[ni2++] = '0' + u % 10; u /= 10; } }
        for (int i = ni2-1; i >= 0; i--) r[n++] = num2[i];
        const char* suf = ",\"free_memory\":";
        while (*suf) r[n++] = *suf++;
        ni2 = 0; u = info.free_memory;
        if (u == 0) num2[ni2++] = '0';
        else { while (u > 0) { num2[ni2++] = '0' + u % 10; u /= 10; } }
        for (int i = ni2-1; i >= 0; i--) r[n++] = num2[i];
        r[n++] = '}'; r[n] = 0;
        resp_len = write_response(response, rpc.id, r);
        break;
    }

    default:
        resp_len = write_response(response, rpc.id,
            "\"method not supported\"");
        break;
    }
}

void web3_server_task(void* arg) {
    (void)arg;
    uart_puts("[web3] JSON-RPC server starting on port 8545\r\n");

    int listen_sock = net_tcp_listen(WEB3_PORT);
    if (listen_sock < 0) {
        uart_puts("[web3] Failed to bind port\r\n");
        return;
    }

    uart_puts("[web3] Listening on port 8545\r\n");

    // Mine genesis block
    current_block.number = 0;
    current_block.timestamp = kernel_uptime_ms() / 1000;
    keccak256(reinterpret_cast<const uint8_t*>("solarpunk-genesis"), 17,
              current_block.hash);

    char req_buf[512];
    char resp_buf[512];

    while (1) {
        int client = net_tcp_accept(listen_sock);
        if (client >= 0) {
            int len = net_tcp_recv(client,
                reinterpret_cast<uint8_t*>(req_buf), sizeof(req_buf) - 1);
            if (len > 0) {
                req_buf[len] = 0;
                int resp_len = 0;
                handle_rpc(req_buf, resp_buf, resp_len);
                if (resp_len > 0) {
                    net_tcp_send(client,
                        reinterpret_cast<uint8_t*>(resp_buf), resp_len);
                }
            }
            net_tcp_close(client);
        }

        // Advance block every ~12 seconds (like Ethereum)
        uint32_t now = kernel_uptime_ms() / 1000;
        if (now - current_block.timestamp >= 12) {
            current_block.parent_hash = current_block.hash;
            current_block.number++;
            current_block.timestamp = now;
            // Hash the block number as new block hash
            keccak256(reinterpret_cast<const uint8_t*>(&current_block.number),
                      8, current_block.hash);
        }

        Scheduler::instance().sleep_ms(100);
    }
}

} // namespace solarpunk
