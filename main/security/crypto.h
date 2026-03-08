#pragma once

#include <cstdint>
#include <cstddef>

// AES-256-GCM encryption for mesh messages and stored data
// Uses mbedtls (built into ESP-IDF)

// Initialize crypto subsystem with mesh key
void crypto_init();

// Encrypt data with AES-256-GCM
// Output format: [12-byte IV][ciphertext][16-byte tag]
// Returns total output length, or -1 on error
int crypto_encrypt(const uint8_t* plain, int plain_len,
                   uint8_t* out, int out_size);

// Decrypt data encrypted with crypto_encrypt
// Input format: [12-byte IV][ciphertext][16-byte tag]
// Returns plaintext length, or -1 on error (tampered/wrong key)
int crypto_decrypt(const uint8_t* enc, int enc_len,
                   uint8_t* out, int out_size);

// Check API auth token
bool crypto_check_auth(const char* token);

// Get the auth token (for display)
const char* crypto_get_token();
