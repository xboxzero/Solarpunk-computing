#include "net.h"
#include "../kernel/kernel.h"
#include "../kernel/scheduler.h"
#include "../drivers/uart.h"

namespace solarpunk {

static TcpSocket sockets[MAX_SOCKETS];
static IpAddr local_ip = {{192, 168, 1, 100}};
static bool net_ready = false;

void net_init() {
    for (int i = 0; i < MAX_SOCKETS; i++) {
        sockets[i].id = i;
        sockets[i].connected = false;
        sockets[i].rx_len = 0;
        sockets[i].tx_len = 0;
    }

#if PLATFORM_ESP32
    // ESP32: Initialize WiFi hardware
    uart_puts("[net] ESP32 WiFi init...\r\n");
    // TODO: Configure WiFi peripheral registers
    // For now, mark as ready for the framework
#elif PLATFORM_PICO2
    // Pico 2: Uses external SPI Ethernet/WiFi module
    uart_puts("[net] Pico2 network init (SPI)...\r\n");
#endif

    net_ready = true;
    uart_puts("[net] Network stack initialized\r\n");
}

void net_task(void* arg) {
    (void)arg;
    uart_puts("[net] Network task running\r\n");

    while (1) {
        // Poll for incoming packets
        if (net_ready) {
            // Process incoming data on all sockets
            for (int i = 0; i < MAX_SOCKETS; i++) {
                if (sockets[i].connected && sockets[i].tx_len > 0) {
                    // Transmit pending data
                    // Platform-specific TX here
                    sockets[i].tx_len = 0;
                }
            }
        }

        Scheduler::instance().sleep_ms(10);
    }
}

int net_tcp_listen(uint16_t port) {
    for (int i = 0; i < MAX_SOCKETS; i++) {
        if (!sockets[i].connected) {
            sockets[i].local_port = port;
            sockets[i].connected = false;
            sockets[i].rx_len = 0;
            sockets[i].tx_len = 0;
            return i;
        }
    }
    return -1;
}

int net_tcp_accept(int listen_id) {
    if (listen_id < 0 || listen_id >= MAX_SOCKETS) return -1;
    // In real implementation, this would block until connection
    // For now, return the socket if it becomes connected
    if (sockets[listen_id].connected) {
        return listen_id;
    }
    return -1;
}

int net_tcp_send(int sock_id, const uint8_t* data, uint16_t len) {
    if (sock_id < 0 || sock_id >= MAX_SOCKETS) return -1;
    if (!sockets[sock_id].connected) return -1;

    uint16_t space = sizeof(sockets[sock_id].tx_buf) - sockets[sock_id].tx_len;
    if (len > space) len = space;

    for (uint16_t i = 0; i < len; i++) {
        sockets[sock_id].tx_buf[sockets[sock_id].tx_len++] = data[i];
    }
    return len;
}

int net_tcp_recv(int sock_id, uint8_t* buf, uint16_t max_len) {
    if (sock_id < 0 || sock_id >= MAX_SOCKETS) return -1;
    if (!sockets[sock_id].connected) return -1;

    uint16_t len = sockets[sock_id].rx_len;
    if (len > max_len) len = max_len;

    for (uint16_t i = 0; i < len; i++) {
        buf[i] = sockets[sock_id].rx_buf[i];
    }

    // Shift remaining data
    uint16_t remaining = sockets[sock_id].rx_len - len;
    for (uint16_t i = 0; i < remaining; i++) {
        sockets[sock_id].rx_buf[i] = sockets[sock_id].rx_buf[len + i];
    }
    sockets[sock_id].rx_len = remaining;

    return len;
}

void net_tcp_close(int sock_id) {
    if (sock_id >= 0 && sock_id < MAX_SOCKETS) {
        sockets[sock_id].connected = false;
        sockets[sock_id].rx_len = 0;
        sockets[sock_id].tx_len = 0;
    }
}

IpAddr net_get_ip() {
    return local_ip;
}

} // namespace solarpunk
