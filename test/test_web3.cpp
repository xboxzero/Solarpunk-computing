#include "../web3/web3.h"
#include <cstring>

extern void test_assert(bool condition, const char* name);

static void hash_to_hex(const solarpunk::Hash256& h, char* out) {
    const char* hex = "0123456789abcdef";
    for (int i = 0; i < 32; i++) {
        out[i*2]     = hex[h.bytes[i] >> 4];
        out[i*2 + 1] = hex[h.bytes[i] & 0xF];
    }
    out[64] = 0;
}

void test_web3() {
    using namespace solarpunk;

    // Test Keccak-256 with known vectors
    // keccak256("") = c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
    {
        Hash256 hash;
        keccak256(nullptr, 0, hash);
        // Note: passing nullptr with len 0 - test the empty input
        uint8_t empty[] = {};
        keccak256(empty, 0, hash);
        char hex[65];
        hash_to_hex(hash, hex);
        test_assert(strcmp(hex,
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470") == 0,
            "Keccak-256 empty string");
    }

    // keccak256("abc") = 4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45
    {
        Hash256 hash;
        const uint8_t data[] = {'a', 'b', 'c'};
        keccak256(data, 3, hash);
        char hex[65];
        hash_to_hex(hash, hex);
        test_assert(strcmp(hex,
            "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45") == 0,
            "Keccak-256 'abc'");
    }

    // Test RPC method parsing
    test_assert(parse_rpc_method("eth_blockNumber") == RpcMethod::ETH_BLOCK_NUMBER,
        "Parse eth_blockNumber");
    test_assert(parse_rpc_method("web3_clientVersion") == RpcMethod::WEB3_CLIENT_VERSION,
        "Parse web3_clientVersion");
    test_assert(parse_rpc_method("sp_systemInfo") == RpcMethod::SP_SYSTEM_INFO,
        "Parse sp_systemInfo");
    test_assert(parse_rpc_method("unknown_method") == RpcMethod::UNKNOWN,
        "Parse unknown method");
    test_assert(parse_rpc_method("eth_chainId") == RpcMethod::ETH_CHAIN_ID,
        "Parse eth_chainId");
}
