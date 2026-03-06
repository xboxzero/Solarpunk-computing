#include "terminal.h"
#include "../kernel/kernel.h"
#include "../kernel/scheduler.h"
#include "../kernel/memory.h"
#include "../drivers/uart.h"
#include "../container/container.h"
#include "../web3/web3.h"

namespace solarpunk {

// Simple string compare
static bool streq(const char* a, const char* b) {
    while (*a && *b) { if (*a++ != *b++) return false; }
    return *a == *b;
}

static bool starts_with(const char* str, const char* prefix) {
    while (*prefix) {
        if (*str++ != *prefix++) return false;
    }
    return true;
}

static void cmd_help() {
    uart_puts("Commands:\r\n");
    uart_puts("  help          - Show this help\r\n");
    uart_puts("  info          - System information\r\n");
    uart_puts("  mem           - Memory usage\r\n");
    uart_puts("  tasks         - List running tasks\r\n");
    uart_puts("  containers    - List containers\r\n");
    uart_puts("  create <name> - Create container\r\n");
    uart_puts("  stop <id>     - Stop container\r\n");
    uart_puts("  destroy <id>  - Destroy container\r\n");
    uart_puts("  hash <text>   - Keccak-256 hash\r\n");
    uart_puts("  block         - Current block info\r\n");
    uart_puts("  reboot        - Reboot system\r\n");
}

static void cmd_info() {
    auto info = kernel_info();
    uart_puts("Platform:    ");
    uart_puts(info.platform);
    uart_puts("\r\nUptime:      ");
    uart_put_dec(info.uptime_ms / 1000);
    uart_puts("s\r\nCPU:         ");
    uart_put_dec(info.cpu_freq / 1000000);
    uart_puts(" MHz\r\nTasks:       ");
    uart_put_dec(info.task_count);
    uart_puts("\r\nFree memory: ");
    uart_put_dec(info.free_memory);
    uart_puts(" bytes\r\n");
}

static void cmd_mem() {
    auto& mm = MemoryManager::instance();
    uart_puts("Heap used: ");
    uart_put_dec(mm.used_bytes());
    uart_puts(" / ");
    uart_put_dec(mm.free_bytes() + mm.used_bytes());
    uart_puts(" bytes (");
    uart_put_dec(mm.free_bytes());
    uart_puts(" free)\r\n");
}

static void cmd_tasks() {
    uart_puts("ID  State    Pri  Container  Name\r\n");
    uart_puts("--  -------  ---  ---------  ----\r\n");
    // Access tasks through scheduler - simplified view
    uart_puts("(task list via scheduler)\r\n");
}

static void cmd_containers() {
    auto& cr = ContainerRuntime::instance();
    uart_puts("ID  State    Net  GPIO  Name\r\n");
    uart_puts("--  -------  ---  ----  ----\r\n");
    for (int i = 0; i < MAX_CONTAINERS; i++) {
        Container* c = cr.get(i);
        if (!c) continue;
        uart_put_dec(c->id);
        uart_puts("   ");
        switch (c->state) {
            case ContainerState::CREATED: uart_puts("created "); break;
            case ContainerState::RUNNING: uart_puts("running "); break;
            case ContainerState::STOPPED: uart_puts("stopped "); break;
            default: break;
        }
        uart_puts(" ");
        uart_puts(c->net_allowed ? "yes" : "no ");
        uart_puts("  ");
        uart_puts(c->gpio_allowed ? "yes " : "no  ");
        uart_puts("  ");
        uart_puts(c->name);
        uart_puts("\r\n");
    }
}

static void cmd_hash(const char* text) {
    Hash256 hash;
    keccak256(reinterpret_cast<const uint8_t*>(text),
              0, hash);
    // Calculate length
    uint32_t len = 0;
    const char* p = text;
    while (*p++) len++;
    keccak256(reinterpret_cast<const uint8_t*>(text), len, hash);

    uart_puts("0x");
    for (int i = 0; i < 32; i++) {
        uint8_t hi = hash.bytes[i] >> 4;
        uint8_t lo = hash.bytes[i] & 0xF;
        uart_putc(hi < 10 ? '0' + hi : 'a' + hi - 10);
        uart_putc(lo < 10 ? '0' + lo : 'a' + lo - 10);
    }
    uart_puts("\r\n");
}

void terminal_task(void* arg) {
    (void)arg;

    uart_puts("\r\n");
    uart_puts("Solarpunk Terminal v0.1\r\n");
    uart_puts("Type 'help' for commands.\r\n");

    char line[128];
    int pos = 0;

    while (1) {
        uart_puts("sp> ");
        pos = 0;

        // Read line
        while (1) {
            if (!uart_available()) {
                Scheduler::instance().sleep_ms(50);
                continue;
            }

            int c = uart_getc();
            if (c < 0) continue;

            if (c == '\r' || c == '\n') {
                uart_puts("\r\n");
                line[pos] = 0;
                break;
            }
            if (c == 127 || c == 8) { // Backspace
                if (pos > 0) {
                    pos--;
                    uart_puts("\b \b");
                }
                continue;
            }
            if (pos < 126) {
                line[pos++] = c;
                uart_putc(c);
            }
        }

        // Parse and execute
        if (pos == 0) continue;

        if (streq(line, "help"))           cmd_help();
        else if (streq(line, "info"))      cmd_info();
        else if (streq(line, "mem"))       cmd_mem();
        else if (streq(line, "tasks"))     cmd_tasks();
        else if (streq(line, "containers")) cmd_containers();
        else if (starts_with(line, "hash ")) cmd_hash(line + 5);
        else if (streq(line, "block")) {
            uart_puts("Block number: ");
            uart_put_dec(0); // Would need access to web3 block state
            uart_puts("\r\n");
        }
        else if (streq(line, "reboot")) {
            uart_puts("Rebooting...\r\n");
#if PLATFORM_PICO2
            *reinterpret_cast<volatile uint32_t*>(0xE000ED0C) = 0x05FA0004;
#elif PLATFORM_ESP32
            *reinterpret_cast<volatile uint32_t*>(0x3FF480D4) = 0;
#endif
        }
        else {
            uart_puts("Unknown command: ");
            uart_puts(line);
            uart_puts("\r\nType 'help' for available commands.\r\n");
        }
    }
}

} // namespace solarpunk
