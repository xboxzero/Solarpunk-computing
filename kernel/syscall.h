#pragma once

#include "kernel.h"

namespace solarpunk {

// Syscall numbers
enum class Syscall : uint8_t {
    YIELD       = 0,
    SLEEP       = 1,
    ALLOC       = 2,
    FREE        = 3,
    SEND        = 4,  // IPC send
    RECV        = 5,  // IPC receive
    NET_OPEN    = 10,
    NET_SEND    = 11,
    NET_RECV    = 12,
    NET_CLOSE   = 13,
    UART_WRITE  = 20,
    UART_READ   = 21,
    GPIO_SET    = 22,
    GPIO_GET    = 23,
    INFO        = 30,
    CONTAINER   = 40, // Container operations
};

struct SyscallArgs {
    Syscall  num;
    uint32_t arg0;
    uint32_t arg1;
    uint32_t arg2;
    uint32_t ret;
};

// IPC message
struct Message {
    uint8_t  src_task;
    uint8_t  dst_task;
    uint16_t type;
    uint32_t data[4];
};

void syscall_dispatch(SyscallArgs& args);

} // namespace solarpunk
