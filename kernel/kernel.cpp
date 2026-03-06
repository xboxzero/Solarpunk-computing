#include "kernel.h"
#include "scheduler.h"
#include "memory.h"
#include "../drivers/uart.h"
#include "../terminal/terminal.h"
#include "../net/net.h"
#include "../web3/web3.h"
#include "../container/container.h"

// Heap memory
static uint8_t heap_memory[solarpunk::HEAP_SIZE];

namespace solarpunk {

static volatile uint32_t uptime_ms = 0;

void kernel_init() {
    // Initialize memory allocator
    MemoryManager::instance().init(heap_memory, HEAP_SIZE);

    // Initialize UART for terminal
    uart_init(115200);
    uart_puts("\r\n");
    uart_puts("========================================\r\n");
    uart_puts("  Solarpunk Computing OS v0.1\r\n");
    uart_puts("  Bare-metal Web3 Microkernel\r\n");
#if PLATFORM_PICO2
    uart_puts("  Platform: Pi Pico 2 (RP2350)\r\n");
#elif PLATFORM_ESP32
    uart_puts("  Platform: ESP32\r\n");
#else
    uart_puts("  Platform: Host (test mode)\r\n");
#endif
    uart_puts("========================================\r\n");

    // Initialize scheduler
    Scheduler::instance().init();

    // Initialize network stack
    net_init();

    // Initialize container runtime
    ContainerRuntime::instance().init();
}

SystemInfo kernel_info() {
    SystemInfo info;
    info.uptime_ms = uptime_ms;
    info.free_memory = MemoryManager::instance().free_bytes();
    info.task_count = Scheduler::instance().task_count();
    info.cpu_freq = CPU_FREQ_HZ;
#if PLATFORM_PICO2
    info.platform = "Pi Pico 2 (RP2350)";
#elif PLATFORM_ESP32
    info.platform = "ESP32";
#else
    info.platform = "Host";
#endif
    return info;
}

uint32_t kernel_uptime_ms() {
    return uptime_ms;
}

} // namespace solarpunk

// C linkage entry points

extern "C" void kernel_main() {
    using namespace solarpunk;

    kernel_init();

    // Create system tasks
    auto& sched = Scheduler::instance();

    // Terminal shell (container 0 = kernel)
    sched.create_task("terminal", terminal_task, nullptr, 2, 0);

    // Web3 JSON-RPC server (container 1 = web3)
    sched.create_task("web3", web3_server_task, nullptr, 1, 1);

    // Network handler
    sched.create_task("net", net_task, nullptr, 1, 0);

    uart_puts("[kernel] All tasks created. Starting scheduler.\r\n");

    // Start scheduling (never returns)
    sched.start();
}

extern "C" void systick_handler() {
    solarpunk::uptime_ms++;
    solarpunk::Scheduler::instance().tick();
}

extern "C" void fault_handler(void* frame) {
    solarpunk::uart_puts("[FAULT] System halted.\r\n");
    while (1) {}
}
