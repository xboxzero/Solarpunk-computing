#pragma once

#ifdef PLATFORM_HOST
#include <cstdint>
#include <cstddef>
#else
#include <stdint.h>
#include <stddef.h>
#endif

namespace solarpunk {

// Platform detection
#if defined(__ARM_ARCH_8M_MAIN__)
    #define PLATFORM_PICO2 1
    constexpr uint32_t CPU_FREQ_HZ = 125000000;
    constexpr uint32_t RAM_SIZE = 520 * 1024;
#elif defined(__XTENSA__)
    #define PLATFORM_ESP32 1
    constexpr uint32_t CPU_FREQ_HZ = 240000000;
    constexpr uint32_t RAM_SIZE = 520 * 1024;
#else
    #define PLATFORM_HOST 1
    constexpr uint32_t CPU_FREQ_HZ = 1000000000;
    constexpr uint32_t RAM_SIZE = 64 * 1024 * 1024;
#endif

constexpr uint32_t TICK_HZ = 1000;  // 1ms tick
constexpr uint32_t MAX_TASKS = 16;
constexpr uint32_t TASK_STACK_SIZE = 4096;
constexpr uint32_t HEAP_SIZE = 128 * 1024;

// Task states
enum class TaskState : uint8_t {
    DEAD = 0,
    READY,
    RUNNING,
    BLOCKED,
    SUSPENDED
};

// Task control block
struct Task {
    uint32_t* stack_ptr;
    uint32_t  stack[TASK_STACK_SIZE / sizeof(uint32_t)];
    TaskState state;
    uint8_t   priority;
    uint8_t   container_id;
    uint8_t   id;
    const char* name;
    void (*entry)(void*);
    void* arg;
    uint32_t  wake_tick;
};

// System info
struct SystemInfo {
    uint32_t uptime_ms;
    uint32_t free_memory;
    uint32_t task_count;
    uint32_t cpu_freq;
    const char* platform;
};

// Kernel API
void kernel_init();
SystemInfo kernel_info();
uint32_t kernel_uptime_ms();

} // namespace solarpunk

// C linkage for assembly entry
extern "C" {
    void kernel_main();
    void systick_handler();
    void fault_handler(void* frame);
}
