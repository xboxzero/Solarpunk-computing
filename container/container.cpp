#include "container.h"
#include "../kernel/scheduler.h"
#include "../kernel/memory.h"
#include "../drivers/uart.h"

namespace solarpunk {

ContainerRuntime& ContainerRuntime::instance() {
    static ContainerRuntime cr;
    return cr;
}

void ContainerRuntime::init() {
    for (int i = 0; i < MAX_CONTAINERS; i++) {
        containers_[i].id = i;
        containers_[i].state = ContainerState::EMPTY;
        containers_[i].name = nullptr;
        containers_[i].mem_base = nullptr;
        containers_[i].mem_size = 0;
        containers_[i].mem_used = 0;
        containers_[i].task_count = 0;
        containers_[i].net_allowed = false;
        containers_[i].gpio_allowed = false;
    }

    // Container 0 is the kernel container (always exists)
    containers_[0].state = ContainerState::RUNNING;
    containers_[0].name = "kernel";
    containers_[0].net_allowed = true;
    containers_[0].gpio_allowed = true;

    uart_puts("[container] Runtime initialized\r\n");
}

int ContainerRuntime::create(const char* name, uint32_t mem_limit) {
    for (int i = 1; i < MAX_CONTAINERS; i++) {
        if (containers_[i].state == ContainerState::EMPTY) {
            containers_[i].name = name;
            containers_[i].mem_size = mem_limit;
            containers_[i].mem_base = MemoryManager::instance().alloc(mem_limit);
            if (!containers_[i].mem_base) {
                uart_puts("[container] Failed to allocate memory for: ");
                uart_puts(name);
                uart_puts("\r\n");
                return -1;
            }
            containers_[i].mem_used = 0;
            containers_[i].state = ContainerState::CREATED;
            containers_[i].task_count = 0;
            containers_[i].net_allowed = false;
            containers_[i].gpio_allowed = false;

            uart_puts("[container] Created: ");
            uart_puts(name);
            uart_puts(" (");
            uart_put_dec(mem_limit);
            uart_puts(" bytes)\r\n");

            return i;
        }
    }
    return -1;
}

int ContainerRuntime::spawn_task(uint8_t container_id, const char* task_name,
                                  void (*entry)(void*), void* arg, uint8_t priority) {
    if (container_id >= MAX_CONTAINERS) return -1;
    Container& c = containers_[container_id];
    if (c.state == ContainerState::EMPTY) return -1;
    if (c.task_count >= 4) return -1;

    int task_id = Scheduler::instance().create_task(task_name, entry, arg,
                                                      priority, container_id);
    if (task_id >= 0) {
        c.task_ids[c.task_count++] = task_id;
        if (c.state == ContainerState::CREATED) {
            c.state = ContainerState::RUNNING;
        }
    }
    return task_id;
}

void ContainerRuntime::stop(uint8_t id) {
    if (id == 0 || id >= MAX_CONTAINERS) return; // Can't stop kernel
    Container& c = containers_[id];
    if (c.state != ContainerState::RUNNING) return;

    for (int i = 0; i < c.task_count; i++) {
        Scheduler::instance().kill_task(c.task_ids[i]);
    }
    c.state = ContainerState::STOPPED;

    uart_puts("[container] Stopped: ");
    uart_puts(c.name);
    uart_puts("\r\n");
}

void ContainerRuntime::destroy(uint8_t id) {
    if (id == 0 || id >= MAX_CONTAINERS) return;
    stop(id);

    Container& c = containers_[id];
    if (c.mem_base) {
        MemoryManager::instance().free(c.mem_base);
        c.mem_base = nullptr;
    }
    c.state = ContainerState::EMPTY;
    c.task_count = 0;

    uart_puts("[container] Destroyed: ");
    uart_puts(c.name);
    uart_puts("\r\n");
}

void ContainerRuntime::set_net_access(uint8_t id, bool allowed) {
    if (id < MAX_CONTAINERS) containers_[id].net_allowed = allowed;
}

void ContainerRuntime::set_gpio_access(uint8_t id, bool allowed) {
    if (id < MAX_CONTAINERS) containers_[id].gpio_allowed = allowed;
}

Container* ContainerRuntime::get(uint8_t id) {
    if (id < MAX_CONTAINERS && containers_[id].state != ContainerState::EMPTY) {
        return &containers_[id];
    }
    return nullptr;
}

uint8_t ContainerRuntime::count() const {
    uint8_t n = 0;
    for (int i = 0; i < MAX_CONTAINERS; i++) {
        if (containers_[i].state != ContainerState::EMPTY) n++;
    }
    return n;
}

uint8_t ContainerRuntime::find_container_for_task(uint8_t task_id) {
    for (int i = 0; i < MAX_CONTAINERS; i++) {
        if (containers_[i].state == ContainerState::EMPTY) continue;
        for (int j = 0; j < containers_[i].task_count; j++) {
            if (containers_[i].task_ids[j] == task_id) return i;
        }
    }
    return 0; // Default to kernel container
}

bool ContainerRuntime::check_net_permission(uint8_t task_id) {
    return containers_[find_container_for_task(task_id)].net_allowed;
}

bool ContainerRuntime::check_gpio_permission(uint8_t task_id) {
    return containers_[find_container_for_task(task_id)].gpio_allowed;
}

} // namespace solarpunk
