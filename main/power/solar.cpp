// Solarpunk Wearable - Solar + Battery Monitor
// Reads battery and solar panel voltage via ADC.
// Uses a voltage divider: Vbat -> 100K -> ADC -> 100K -> GND
// So ADC reads half the actual voltage.

#include "solar.h"
#include "../config.h"

#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"

static const char* TAG = "solar";

static adc_oneshot_unit_handle_t adc_handle = NULL;
static int battery_mv = 3700;   // Cached readings
static int panel_mv = 0;
static bool charging = false;

void solar_init() {
    adc_oneshot_unit_init_cfg_t init_cfg = {
        .unit_id = ADC_UNIT_1,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_cfg, &adc_handle));

    adc_oneshot_chan_cfg_t chan_cfg = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_handle, (adc_channel_t)SP_BATTERY_ADC_PIN, &chan_cfg));
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_handle, (adc_channel_t)SP_SOLAR_ADC_PIN, &chan_cfg));

    solar_update();
    ESP_LOGI(TAG, "Solar monitor init: bat=%dmV, panel=%dmV", battery_mv, panel_mv);
}

void solar_update() {
    int raw = 0;

    // Read battery voltage (through voltage divider, so multiply by 2)
    if (adc_oneshot_read(adc_handle, (adc_channel_t)SP_BATTERY_ADC_PIN, &raw) == ESP_OK) {
        // ESP32-S3 ADC: 0-4095 maps to 0-3100mV at 12dB attenuation
        // Voltage divider halves, so actual = reading * 2
        battery_mv = (raw * 3100 / 4095) * 2;
    }

    // Read solar panel voltage
    if (adc_oneshot_read(adc_handle, (adc_channel_t)SP_SOLAR_ADC_PIN, &raw) == ESP_OK) {
        panel_mv = (raw * 3100 / 4095) * 2;
    }

    // Charging if solar voltage is higher than battery
    charging = (panel_mv > battery_mv + 200);
}

int solar_battery_percent() {
    if (battery_mv >= SP_BATTERY_FULL_MV) return 100;
    if (battery_mv <= SP_BATTERY_EMPTY_MV) return 0;
    return (battery_mv - SP_BATTERY_EMPTY_MV) * 100 /
           (SP_BATTERY_FULL_MV - SP_BATTERY_EMPTY_MV);
}

int solar_battery_mv() {
    return battery_mv;
}

int solar_panel_mv() {
    return panel_mv;
}

bool solar_is_charging() {
    return charging;
}
