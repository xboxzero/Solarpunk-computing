#include "scheduler.h"
#include "../drivers/uart.h"

namespace solarpunk {

Scheduler& Scheduler::instance() {
    static Scheduler s;
    return s;
}

void Scheduler::init() {
    for (int i = 0; i < MAX_TASKS; i++) {
        tasks_[i].state = TaskState::DEAD;
        tasks_[i].id = i;
    }
    current_ = 0;
    ticks_ = 0;
    running_ = false;
}

int Scheduler::create_task(const char* name, void (*entry)(void*), void* arg,
                           uint8_t priority, uint8_t container_id) {
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks_[i].state == TaskState::DEAD) {
            tasks_[i].name = name;
            tasks_[i].entry = entry;
            tasks_[i].arg = arg;
            tasks_[i].priority = priority;
            tasks_[i].container_id = container_id;
            tasks_[i].state = TaskState::READY;
            tasks_[i].wake_tick = 0;
            init_task_stack(tasks_[i]);

            uart_puts("[sched] Task created: ");
            uart_puts(name);
            uart_puts("\r\n");
            return i;
        }
    }
    return -1; // No free slots
}

void Scheduler::kill_task(uint8_t id) {
    if (id < MAX_TASKS) {
        tasks_[id].state = TaskState::DEAD;
    }
}

void Scheduler::init_task_stack(Task& task) {
    // Set up initial stack frame so context_switch can pop into the task
    uint32_t* sp = &task.stack[TASK_STACK_SIZE / sizeof(uint32_t) - 1];

    // Exception return frame (ARM Cortex-M style)
    *(--sp) = 0x01000000;                   // xPSR (thumb bit)
    *(--sp) = reinterpret_cast<uintptr_t>(reinterpret_cast<void*>(task.entry)); // PC
    *(--sp) = 0;                             // LR
    *(--sp) = 0;                             // R12
    *(--sp) = 0;                             // R3
    *(--sp) = 0;                             // R2
    *(--sp) = 0;                             // R1
    *(--sp) = reinterpret_cast<uintptr_t>(task.arg); // R0 (first argument)

    // Callee-saved registers
    for (int i = 0; i < 8; i++) {
        *(--sp) = 0;                         // R4-R11
    }

    task.stack_ptr = sp;
}

void Scheduler::yield() {
    if (running_) {
        tasks_[current_].state = TaskState::READY;
        schedule();
    }
}

void Scheduler::sleep_ms(uint32_t ms) {
    if (running_) {
        tasks_[current_].state = TaskState::BLOCKED;
        tasks_[current_].wake_tick = ticks_ + ms;
        schedule();
    }
}

void Scheduler::tick() {
    ticks_++;

    // Wake up sleeping tasks
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks_[i].state == TaskState::BLOCKED &&
            tasks_[i].wake_tick != 0 &&
            ticks_ >= tasks_[i].wake_tick) {
            tasks_[i].state = TaskState::READY;
            tasks_[i].wake_tick = 0;
        }
    }
}

void Scheduler::start() {
    running_ = true;

    // Find first ready task
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks_[i].state == TaskState::READY) {
            current_ = i;
            tasks_[i].state = TaskState::RUNNING;
            // Jump to task (platform-specific)
#if PLATFORM_PICO2
            // Restore context and branch to task
            asm volatile(
                "msr psp, %0\n"
                "mov r0, #3\n"     // Use PSP, unprivileged
                "msr control, r0\n"
                "isb\n"
                "pop {r4-r11}\n"
                "pop {r0-r3, r12, lr}\n"
                "pop {pc}\n"
                :
                : "r"(tasks_[i].stack_ptr)
            );
#else
            // Host mode: just call the function
            tasks_[i].entry(tasks_[i].arg);
#endif
            break;
        }
    }

    // Fallback loop
    while (1) {
        schedule();
    }
}

void Scheduler::schedule() {
    // Simple priority-based round-robin
    uint8_t best = 0xFF;
    uint8_t best_pri = 0;

    for (int i = 0; i < MAX_TASKS; i++) {
        uint8_t idx = (current_ + 1 + i) % MAX_TASKS;
        if (tasks_[idx].state == TaskState::READY &&
            tasks_[idx].priority >= best_pri) {
            best = idx;
            best_pri = tasks_[idx].priority;
        }
    }

    if (best != 0xFF && best != current_) {
        Task* next = &tasks_[best];
        next->state = TaskState::RUNNING;
        if (tasks_[current_].state == TaskState::RUNNING) {
            tasks_[current_].state = TaskState::READY;
        }
        context_switch(next);
    }
}

void Scheduler::context_switch(Task* next) {
#if PLATFORM_PICO2
    Task* prev = &tasks_[current_];
    current_ = next->id;

    asm volatile(
        // Save current context
        "mrs r0, psp\n"
        "stmdb r0!, {r4-r11}\n"
        "str r0, [%0]\n"
        // Load next context
        "ldr r0, [%1]\n"
        "ldmia r0!, {r4-r11}\n"
        "msr psp, r0\n"
        :
        : "r"(&prev->stack_ptr), "r"(&next->stack_ptr)
        : "r0", "memory"
    );
#else
    // Host mode: cooperative (task must yield)
    current_ = next->id;
#endif
}

Task* Scheduler::current_task() {
    return &tasks_[current_];
}

uint32_t Scheduler::task_count() const {
    uint32_t count = 0;
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks_[i].state != TaskState::DEAD) count++;
    }
    return count;
}

} // namespace solarpunk
