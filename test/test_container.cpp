#include "../container/container.h"
#include "../kernel/memory.h"
#include "../kernel/scheduler.h"

extern void test_assert(bool condition, const char* name);

static uint8_t container_test_heap[65536];

static void dummy_task(void*) {}

void test_container() {
    using namespace solarpunk;

    // Init dependencies
    MemoryManager::instance().init(container_test_heap, sizeof(container_test_heap));
    Scheduler::instance().init();
    ContainerRuntime::instance().init();

    auto& cr = ContainerRuntime::instance();

    // Kernel container exists
    test_assert(cr.get(0) != nullptr, "Kernel container exists");
    test_assert(cr.get(0)->state == ContainerState::RUNNING, "Kernel container is running");
    test_assert(cr.get(0)->net_allowed == true, "Kernel has net access");

    // Create container
    int id = cr.create("test-app", 4096);
    test_assert(id > 0, "Create container returns valid id");
    test_assert(cr.get(id) != nullptr, "Created container exists");
    test_assert(cr.get(id)->state == ContainerState::CREATED, "New container is CREATED");
    test_assert(cr.get(id)->net_allowed == false, "New container has no net by default");

    // Set permissions
    cr.set_net_access(id, true);
    test_assert(cr.get(id)->net_allowed == true, "Net access set to true");

    cr.set_gpio_access(id, true);
    test_assert(cr.get(id)->gpio_allowed == true, "GPIO access set to true");

    // Spawn task in container
    int tid = cr.spawn_task(id, "test-task", dummy_task, nullptr, 1);
    test_assert(tid >= 0, "Spawn task in container");
    test_assert(cr.get(id)->state == ContainerState::RUNNING, "Container now running");

    // Stop container
    cr.stop(id);
    test_assert(cr.get(id)->state == ContainerState::STOPPED, "Container stopped");

    // Destroy container
    cr.destroy(id);
    test_assert(cr.get(id) == nullptr, "Container destroyed");

    // Can't stop kernel
    cr.stop(0);
    test_assert(cr.get(0)->state == ContainerState::RUNNING, "Can't stop kernel container");

    // Count
    test_assert(cr.count() >= 1, "At least kernel container exists");
}
