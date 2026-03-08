#pragma once

#include <cstdint>

// UART is handled by ESP-IDF's built-in driver.
// These wrappers exist for compatibility with the kernel module.

namespace solarpunk {

void uart_init(uint32_t baud);
void uart_putc(char c);
void uart_puts(const char* s);
int  uart_getc();
bool uart_available();

} // namespace solarpunk
