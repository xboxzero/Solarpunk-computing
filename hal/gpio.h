#pragma once

#include <cstdint>

namespace solarpunk {

enum class GpioDir : uint8_t { INPUT = 0, OUTPUT = 1 };
enum class GpioPull : uint8_t { NONE = 0, UP = 1, DOWN = 2 };

void gpio_init(uint8_t pin, GpioDir dir, GpioPull pull = GpioPull::NONE);
void gpio_set(uint8_t pin, bool value);
bool gpio_get(uint8_t pin);
void gpio_toggle(uint8_t pin);

} // namespace solarpunk
