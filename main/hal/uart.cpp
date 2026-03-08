// UART HAL - thin wrapper over ESP-IDF UART driver

#include "uart.h"
#include "driver/uart.h"

namespace solarpunk {

void uart_init(uint32_t baud) {
    uart_config_t cfg = {
        .baud_rate = (int)baud,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    };
    uart_param_config(UART_NUM_0, &cfg);
    uart_driver_install(UART_NUM_0, 256, 0, 0, NULL, 0);
}

void uart_putc(char c) {
    uart_write_bytes(UART_NUM_0, &c, 1);
}

void uart_puts(const char* s) {
    uart_write_bytes(UART_NUM_0, s, strlen(s));
}

int uart_getc() {
    uint8_t c;
    int len = uart_read_bytes(UART_NUM_0, &c, 1, 0);
    return len > 0 ? c : -1;
}

bool uart_available() {
    size_t len = 0;
    uart_get_buffered_data_len(UART_NUM_0, &len);
    return len > 0;
}

} // namespace solarpunk
