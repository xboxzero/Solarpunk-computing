#pragma once

#include "kernel.h"
#include <cstddef>

namespace solarpunk {

// Simple pool-based memory allocator for embedded
// No fragmentation - fixed block sizes
struct MemBlock {
    MemBlock* next;
    uint32_t  size;
    bool      used;
};

class MemoryManager {
public:
    static MemoryManager& instance();

    void  init(void* heap_start, uint32_t heap_size);
    void* alloc(uint32_t size);
    void  free(void* ptr);
    uint32_t free_bytes() const;
    uint32_t used_bytes() const;

private:
    MemoryManager() = default;

    MemBlock* find_free_block(uint32_t size);
    void      coalesce();

    MemBlock* heap_start_ = nullptr;
    uint32_t  heap_size_ = 0;
    uint32_t  used_ = 0;
};

} // namespace solarpunk

// Global operator overloads (must be outside namespace)
void* operator new(size_t size);
void* operator new[](size_t size);
void  operator delete(void* ptr) noexcept;
void  operator delete[](void* ptr) noexcept;
void  operator delete(void* ptr, size_t) noexcept;
void  operator delete[](void* ptr, size_t) noexcept;
