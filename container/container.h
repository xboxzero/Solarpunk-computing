#pragma once

#include "../kernel/kernel.h"

namespace solarpunk {

constexpr uint8_t MAX_CONTAINERS = 8;
constexpr uint32_t CONTAINER_MEM_LIMIT = 16 * 1024; // 16KB per container

enum class ContainerState : uint8_t {
    EMPTY = 0,
    CREATED,
    RUNNING,
    STOPPED
};

struct Container {
    uint8_t         id;
    ContainerState  state;
    const char*     name;
    void*           mem_base;    // Isolated memory region
    uint32_t        mem_size;
    uint32_t        mem_used;
    uint8_t         task_ids[4]; // Up to 4 tasks per container
    uint8_t         task_count;
    bool            net_allowed;
    bool            gpio_allowed;
};

class ContainerRuntime {
public:
    static ContainerRuntime& instance();

    void init();
    int  create(const char* name, uint32_t mem_limit = CONTAINER_MEM_LIMIT);
    int  spawn_task(uint8_t container_id, const char* task_name,
                    void (*entry)(void*), void* arg, uint8_t priority = 1);
    void stop(uint8_t id);
    void destroy(uint8_t id);

    void set_net_access(uint8_t id, bool allowed);
    void set_gpio_access(uint8_t id, bool allowed);

    Container* get(uint8_t id);
    uint8_t count() const;

    // Security: check if current task has permission
    bool check_net_permission(uint8_t task_id);
    bool check_gpio_permission(uint8_t task_id);

private:
    ContainerRuntime() = default;
    uint8_t find_container_for_task(uint8_t task_id);

    Container containers_[MAX_CONTAINERS];
};

} // namespace solarpunk
