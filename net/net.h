#pragma once

#include <cstdint>

namespace solarpunk {

// Minimal TCP/IP types
struct IpAddr {
    uint8_t octets[4];
};

struct TcpSocket {
    uint8_t  id;
    IpAddr   remote_ip;
    uint16_t remote_port;
    uint16_t local_port;
    bool     connected;
    uint8_t  rx_buf[1024];
    uint16_t rx_len;
    uint8_t  tx_buf[1024];
    uint16_t tx_len;
};

constexpr uint8_t MAX_SOCKETS = 4;

void net_init();
void net_task(void* arg);

int  net_tcp_listen(uint16_t port);
int  net_tcp_accept(int listen_id);
int  net_tcp_send(int sock_id, const uint8_t* data, uint16_t len);
int  net_tcp_recv(int sock_id, uint8_t* buf, uint16_t max_len);
void net_tcp_close(int sock_id);

IpAddr net_get_ip();

} // namespace solarpunk
