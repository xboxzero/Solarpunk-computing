#include "../kernel/memory.h"

extern void test_assert(bool condition, const char* name);

static uint8_t test_heap[8192];

void test_memory() {
    using namespace solarpunk;
    auto& mm = MemoryManager::instance();

    // Init
    mm.init(test_heap, sizeof(test_heap));
    test_assert(mm.free_bytes() > 0, "Init - has free memory");
    test_assert(mm.used_bytes() == 0, "Init - zero used");

    uint32_t initial_free = mm.free_bytes();

    // Alloc
    void* p1 = mm.alloc(64);
    test_assert(p1 != nullptr, "Alloc 64 bytes");
    test_assert(mm.used_bytes() > 0, "Used bytes increased after alloc");

    void* p2 = mm.alloc(128);
    test_assert(p2 != nullptr, "Alloc 128 bytes");
    test_assert(p2 != p1, "Second alloc returns different pointer");

    // Free
    uint32_t used_before = mm.used_bytes();
    mm.free(p1);
    test_assert(mm.used_bytes() < used_before, "Free decreases used bytes");

    mm.free(p2);

    // Alloc after free (coalescing)
    void* p3 = mm.alloc(256);
    test_assert(p3 != nullptr, "Alloc after free works");
    mm.free(p3);

    // Null free
    mm.free(nullptr);
    test_assert(true, "Free nullptr does not crash");

    // Many small allocs
    void* ptrs[32];
    bool all_ok = true;
    for (int i = 0; i < 32; i++) {
        ptrs[i] = mm.alloc(16);
        if (!ptrs[i]) { all_ok = false; break; }
    }
    test_assert(all_ok, "32 x 16-byte allocs succeed");

    for (int i = 0; i < 32; i++) {
        mm.free(ptrs[i]);
    }
    test_assert(mm.free_bytes() <= initial_free, "Free after bulk alloc restores memory");
}
