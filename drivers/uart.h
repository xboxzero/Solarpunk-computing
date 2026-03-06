#pragma once

#include <cstdint>

namespace solarpunk {

void uart_init(uint32_t baud);
void uart_putc(char c);
void uart_puts(const char* s);
void uart_put_hex(uint32_t val);
void uart_put_dec(uint32_t val);
int  uart_getc();       // Returns -1 if no data
bool uart_available();

} // namespace solarpunk
