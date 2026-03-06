#include "gpio.h"
#include "../kernel/kernel.h"

namespace solarpunk {

#if PLATFORM_PICO2

static constexpr uint32_t SIO_BASE = 0xD0000000;
static constexpr uint32_t PADS_BANK0 = 0x4001C000;
static constexpr uint32_t IO_BANK0   = 0x40014000;

void gpio_init(uint8_t pin, GpioDir dir, GpioPull pull) {
    // Set pad configuration
    volatile uint32_t* pad = reinterpret_cast<volatile uint32_t*>(
        PADS_BANK0 + 4 + pin * 4
    );
    uint32_t pad_val = (1 << 6);  // IE (input enable)
    if (pull == GpioPull::UP)   pad_val |= (1 << 3);
    if (pull == GpioPull::DOWN) pad_val |= (1 << 2);
    if (dir == GpioDir::OUTPUT) pad_val |= (1 << 7);  // OD
    *pad = pad_val;

    // Set GPIO function to SIO (5)
    volatile uint32_t* ctrl = reinterpret_cast<volatile uint32_t*>(
        IO_BANK0 + 4 + pin * 8
    );
    *ctrl = 5;

    // Set direction
    if (dir == GpioDir::OUTPUT) {
        *reinterpret_cast<volatile uint32_t*>(SIO_BASE + 0x24) = (1 << pin);
    } else {
        *reinterpret_cast<volatile uint32_t*>(SIO_BASE + 0x28) = (1 << pin);
    }
}

void gpio_set(uint8_t pin, bool value) {
    if (value) {
        *reinterpret_cast<volatile uint32_t*>(SIO_BASE + 0x14) = (1 << pin);
    } else {
        *reinterpret_cast<volatile uint32_t*>(SIO_BASE + 0x18) = (1 << pin);
    }
}

bool gpio_get(uint8_t pin) {
    return (*reinterpret_cast<volatile uint32_t*>(SIO_BASE + 0x04) >> pin) & 1;
}

void gpio_toggle(uint8_t pin) {
    *reinterpret_cast<volatile uint32_t*>(SIO_BASE + 0x1C) = (1 << pin);
}

#elif PLATFORM_ESP32

static constexpr uint32_t GPIO_BASE = 0x3FF44000;

void gpio_init(uint8_t pin, GpioDir dir, GpioPull pull) {
    volatile uint32_t* reg = reinterpret_cast<volatile uint32_t*>(
        GPIO_BASE + 0x44 + pin * 4
    );
    if (dir == GpioDir::OUTPUT) {
        *reinterpret_cast<volatile uint32_t*>(GPIO_BASE + 0x20) |= (1 << pin);
    }
    (void)pull;
}

void gpio_set(uint8_t pin, bool value) {
    if (value) {
        *reinterpret_cast<volatile uint32_t*>(GPIO_BASE + 0x08) = (1 << pin);
    } else {
        *reinterpret_cast<volatile uint32_t*>(GPIO_BASE + 0x0C) = (1 << pin);
    }
}

bool gpio_get(uint8_t pin) {
    return (*reinterpret_cast<volatile uint32_t*>(GPIO_BASE + 0x3C) >> pin) & 1;
}

void gpio_toggle(uint8_t pin) {
    gpio_set(pin, !gpio_get(pin));
}

#else // HOST

void gpio_init(uint8_t, GpioDir, GpioPull) {}
void gpio_set(uint8_t, bool) {}
bool gpio_get(uint8_t) { return false; }
void gpio_toggle(uint8_t) {}

#endif

} // namespace solarpunk
