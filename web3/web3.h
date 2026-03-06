#pragma once

#include <cstdint>

namespace solarpunk {

// Ethereum-compatible types
struct Hash256 {
    uint8_t bytes[32];
};

struct Address {
    uint8_t bytes[20];
};

struct Transaction {
    uint64_t nonce;
    uint64_t gas_price;
    uint64_t gas_limit;
    Address  to;
    uint64_t value;
    uint8_t  data[256];
    uint16_t data_len;
    Hash256  hash;
};

struct Block {
    uint64_t number;
    Hash256  hash;
    Hash256  parent_hash;
    uint64_t timestamp;
    uint32_t tx_count;
};

// Keccak-256 hash
void keccak256(const uint8_t* data, uint32_t len, Hash256& out);

// JSON-RPC server
constexpr uint16_t WEB3_PORT = 8545;

void web3_server_task(void* arg);

// Supported RPC methods
enum class RpcMethod : uint8_t {
    UNKNOWN = 0,
    ETH_BLOCK_NUMBER,
    ETH_GET_BALANCE,
    ETH_SEND_TRANSACTION,
    ETH_GET_BLOCK,
    ETH_CHAIN_ID,
    NET_VERSION,
    WEB3_CLIENT_VERSION,
    SP_SYSTEM_INFO,       // Custom: system info
    SP_CONTAINER_LIST,    // Custom: list containers
};

RpcMethod parse_rpc_method(const char* method);

} // namespace solarpunk
