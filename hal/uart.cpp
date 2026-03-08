#include "uart.h"
#include "../kernel/kernel.h"

#if PLATFORM_HOST
#include <cstdio>
#endif

namespace solarpunk {

#if PLATFORM_PICO2

// RP2350 UART0 registers
static constexpr uint32_t UART0_BASE = 0x40034000;
static constexpr uint32_t UART_DR    = 0x00;
static constexpr uint32_t UART_FR    = 0x18;
static constexpr uint32_t UART_IBRD  = 0x24;
static constexpr uint32_t UART_FBRD  = 0x28;
static constexpr uint32_t UART_LCR   = 0x2C;
static constexpr uint32_t UART_CR    = 0x30;

static volatile uint32_t* uart_reg(uint32_t offset) {
    return reinterpret_cast<volatile uint32_t*>(UART0_BASE + offset);
}

void uart_init(uint32_t baud) {
    // Configure GPIO 0,1 for UART
    // IO_BANK0 GPIO0_CTRL = UART function (2)
    *reinterpret_cast<volatile uint32_t*>(0x40014004) = 2;  // GPIO0 -> TX
    *reinterpret_cast<volatile uint32_t*>(0x4001400C) = 2;  // GPIO1 -> RX

    // Set baud rate (125MHz / (16 * baud))
    uint32_t div = CPU_FREQ_HZ / (16 * baud);
    uint32_t frac = ((CPU_FREQ_HZ % (16 * baud)) * 64 + (16 * baud) / 2) / (16 * baud);
    *uart_reg(UART_IBRD) = div;
    *uart_reg(UART_FBRD) = frac;

    // 8N1, enable FIFO
    *uart_reg(UART_LCR) = (3 << 5) | (1 << 4);  // WLEN=8, FEN=1

    // Enable UART, TX, RX
    *uart_reg(UART_CR) = (1 << 0) | (1 << 8) | (1 << 9);
}

void uart_putc(char c) {
    while (*uart_reg(UART_FR) & (1 << 5)) {}  // Wait while TX FIFO full
    *uart_reg(UART_DR) = c;
}

int uart_getc() {
    if (*uart_reg(UART_FR) & (1 << 4)) return -1;  // RX FIFO empty
    return *uart_reg(UART_DR) & 0xFF;
}

bool uart_available() {
    return !(*uart_reg(UART_FR) & (1 << 4));
}

#elif PLATFORM_ESP32

// ESP32 UART0 registers
static constexpr uint32_t UART0_BASE = 0x3FF40000;
static constexpr uint32_t UART_FIFO   = 0x00;
static constexpr uint32_t UART_STATUS = 0x1C;
static constexpr uint32_t UART_CONF0  = 0x20;
static constexpr uint32_t UART_CLKDIV = 0x14;

static volatile uint32_t* uart_reg(uint32_t offset) {
    return reinterpret_cast<volatile uint32_t*>(UART0_BASE + offset);
}

void uart_init(uint32_t baud) {
    *uart_reg(UART_CLKDIV) = CPU_FREQ_HZ / baud;
    *uart_reg(UART_CONF0) = 0x1C;  // 8N1
}

void uart_putc(char c) {
    while ((*uart_reg(UART_STATUS) >> 16) & 0xFF) {}  // Wait TX FIFO
    *uart_reg(UART_FIFO) = c;
}

int uart_getc() {
    if ((*uart_reg(UART_STATUS) & 0xFF) == 0) return -1;
    return *uart_reg(UART_FIFO) & 0xFF;
}

bool uart_available() {
    return (*uart_reg(UART_STATUS) & 0xFF) > 0;
}

#else // HOST

void uart_init(uint32_t baud) {
    (void)baud;
}

void uart_putc(char c) {
    putchar(c);
}

int uart_getc() {
    return -1;
}

bool uart_available() {
    return false;
}

#endif

// Common functions
void uart_puts(const char* s) {
    while (*s) {
        if (*s == '\n') uart_putc('\r');
        uart_putc(*s++);
    }
}

void uart_put_hex(uint32_t val) {
    uart_puts("0x");
    for (int i = 28; i >= 0; i -= 4) {
        uint8_t nibble = (val >> i) & 0xF;
        uart_putc(nibble < 10 ? '0' + nibble : 'a' + nibble - 10);
    }
}

void uart_put_dec(uint32_t val) {
    char buf[12];
    int i = 0;
    if (val == 0) {
        uart_putc('0');
        return;
    }
    while (val > 0) {
        buf[i++] = '0' + (val % 10);
        val /= 10;
    }
    while (--i >= 0) {
        uart_putc(buf[i]);
    }
}

} // namespace solarpunk
