#pragma once

#include "kernel.h"

namespace solarpunk {

class Scheduler {
public:
    static Scheduler& instance();

    void init();
    int  create_task(const char* name, void (*entry)(void*), void* arg,
                     uint8_t priority = 1, uint8_t container_id = 0);
    void kill_task(uint8_t id);
    void yield();
    void sleep_ms(uint32_t ms);
    void tick();
    void start();

    Task* current_task();
    uint32_t task_count() const;
    uint32_t tick_count() const { return ticks_; }

private:
    Scheduler() = default;
    void schedule();
    void context_switch(Task* next);
    void init_task_stack(Task& task);

    Task     tasks_[MAX_TASKS];
    uint8_t  current_ = 0;
    uint32_t ticks_ = 0;
    bool     running_ = false;
};

} // namespace solarpunk
