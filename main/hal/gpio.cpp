// GPIO HAL - thin wrapper over ESP-IDF GPIO driver

#include "gpio.h"
#include "driver/gpio.h"

namespace solarpunk {

void gpio_init(uint8_t pin, GpioDir dir, GpioPull pull) {
    gpio_config_t cfg = {};
    cfg.pin_bit_mask = (1ULL << pin);
    cfg.mode = (dir == GpioDir::OUTPUT) ? GPIO_MODE_OUTPUT : GPIO_MODE_INPUT;

    switch (pull) {
    case GpioPull::UP:   cfg.pull_up_en = GPIO_PULLUP_ENABLE; break;
    case GpioPull::DOWN: cfg.pull_down_en = GPIO_PULLDOWN_ENABLE; break;
    default: break;
    }

    gpio_config(&cfg);
}

void gpio_set(uint8_t pin, bool value) {
    gpio_set_level((gpio_num_t)pin, value ? 1 : 0);
}

bool gpio_get(uint8_t pin) {
    return gpio_get_level((gpio_num_t)pin) != 0;
}

void gpio_toggle(uint8_t pin) {
    gpio_set(pin, !gpio_get(pin));
}

} // namespace solarpunk
