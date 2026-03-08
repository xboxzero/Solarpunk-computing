// Solarpunk Wearable - Crypto Module
// AES-256-GCM for mesh encryption + API auth

#include "crypto.h"
#include "../config.h"

#include "mbedtls/gcm.h"
#include "esp_random.h"
#include "esp_log.h"
#include <cstring>

static const char* TAG = "crypto";
static mbedtls_gcm_context gcm_ctx;
static bool initialized = false;

void crypto_init() {
    mbedtls_gcm_init(&gcm_ctx);

    const uint8_t* key = (const uint8_t*)SP_MESH_KEY;
    int ret = mbedtls_gcm_setkey(&gcm_ctx, MBEDTLS_CIPHER_ID_AES, key, 256);
    if (ret != 0) {
        ESP_LOGE(TAG, "AES-256-GCM key setup failed: %d", ret);
        return;
    }

    initialized = true;
    ESP_LOGI(TAG, "AES-256-GCM encryption ready");
}

int crypto_encrypt(const uint8_t* plain, int plain_len,
                   uint8_t* out, int out_size) {
    if (!initialized) return -1;

    int needed = SP_CRYPTO_IV_LEN + plain_len + SP_CRYPTO_TAG_LEN;
    if (out_size < needed) return -1;

    // Generate random IV
    uint8_t* iv = out;
    esp_fill_random(iv, SP_CRYPTO_IV_LEN);

    // Encrypt
    uint8_t* ciphertext = out + SP_CRYPTO_IV_LEN;
    uint8_t* tag_out = out + SP_CRYPTO_IV_LEN + plain_len;

    int ret = mbedtls_gcm_crypt_and_tag(&gcm_ctx, MBEDTLS_GCM_ENCRYPT,
        plain_len, iv, SP_CRYPTO_IV_LEN,
        NULL, 0,  // no AAD
        plain, ciphertext,
        SP_CRYPTO_TAG_LEN, tag_out);

    if (ret != 0) {
        ESP_LOGE(TAG, "Encrypt failed: %d", ret);
        return -1;
    }

    return needed;
}

int crypto_decrypt(const uint8_t* enc, int enc_len,
                   uint8_t* out, int out_size) {
    if (!initialized) return -1;

    int overhead = SP_CRYPTO_IV_LEN + SP_CRYPTO_TAG_LEN;
    if (enc_len < overhead) return -1;

    int plain_len = enc_len - overhead;
    if (out_size < plain_len) return -1;

    const uint8_t* iv = enc;
    const uint8_t* ciphertext = enc + SP_CRYPTO_IV_LEN;
    const uint8_t* tag_in = enc + SP_CRYPTO_IV_LEN + plain_len;

    int ret = mbedtls_gcm_auth_decrypt(&gcm_ctx, plain_len,
        iv, SP_CRYPTO_IV_LEN,
        NULL, 0,  // no AAD
        tag_in, SP_CRYPTO_TAG_LEN,
        ciphertext, out);

    if (ret != 0) {
        ESP_LOGW(TAG, "Decrypt failed (tampered or wrong key)");
        return -1;
    }

    return plain_len;
}

bool crypto_check_auth(const char* token) {
#if SP_AUTH_ENABLED
    if (!token) return false;
    // Skip "Bearer " prefix if present
    if (strncmp(token, "Bearer ", 7) == 0) token += 7;
    return strcmp(token, SP_AUTH_TOKEN) == 0;
#else
    return true;
#endif
}

const char* crypto_get_token() {
    return SP_AUTH_TOKEN;
}
