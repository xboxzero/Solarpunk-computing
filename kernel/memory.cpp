#include "memory.h"
#include "../drivers/uart.h"

namespace solarpunk {

MemoryManager& MemoryManager::instance() {
    static MemoryManager m;
    return m;
}

void MemoryManager::init(void* heap_start, uint32_t heap_size) {
    heap_start_ = reinterpret_cast<MemBlock*>(heap_start);
    heap_size_ = heap_size;
    used_ = 0;

    // Initialize first free block spanning entire heap
    heap_start_->next = nullptr;
    heap_start_->size = heap_size - sizeof(MemBlock);
    heap_start_->used = false;
}

MemBlock* MemoryManager::find_free_block(uint32_t size) {
    MemBlock* block = heap_start_;
    while (block) {
        if (!block->used && block->size >= size) {
            return block;
        }
        block = block->next;
    }
    return nullptr;
}

void* MemoryManager::alloc(uint32_t size) {
    // Align to 4 bytes
    size = (size + 3) & ~3;

    MemBlock* block = find_free_block(size);
    if (!block) {
        return nullptr;
    }

    // Split block if large enough
    if (block->size > size + sizeof(MemBlock) + 16) {
        MemBlock* new_block = reinterpret_cast<MemBlock*>(
            reinterpret_cast<uint8_t*>(block) + sizeof(MemBlock) + size
        );
        new_block->next = block->next;
        new_block->size = block->size - size - sizeof(MemBlock);
        new_block->used = false;

        block->next = new_block;
        block->size = size;
    }

    block->used = true;
    used_ += block->size + sizeof(MemBlock);

    return reinterpret_cast<uint8_t*>(block) + sizeof(MemBlock);
}

void MemoryManager::free(void* ptr) {
    if (!ptr) return;

    MemBlock* block = reinterpret_cast<MemBlock*>(
        reinterpret_cast<uint8_t*>(ptr) - sizeof(MemBlock)
    );

    if (block->used) {
        block->used = false;
        used_ -= block->size + sizeof(MemBlock);
        coalesce();
    }
}

void MemoryManager::coalesce() {
    MemBlock* block = heap_start_;
    while (block && block->next) {
        if (!block->used && !block->next->used) {
            block->size += sizeof(MemBlock) + block->next->size;
            block->next = block->next->next;
        } else {
            block = block->next;
        }
    }
}

uint32_t MemoryManager::free_bytes() const {
    return heap_size_ - used_;
}

uint32_t MemoryManager::used_bytes() const {
    return used_;
}

} // namespace solarpunk

// Global new/delete operators (must be outside namespace)
void* operator new(size_t size) {
    return solarpunk::MemoryManager::instance().alloc(size);
}

void* operator new[](size_t size) {
    return solarpunk::MemoryManager::instance().alloc(size);
}

void operator delete(void* ptr) noexcept {
    solarpunk::MemoryManager::instance().free(ptr);
}

void operator delete[](void* ptr) noexcept {
    solarpunk::MemoryManager::instance().free(ptr);
}

void operator delete(void* ptr, size_t) noexcept {
    solarpunk::MemoryManager::instance().free(ptr);
}

void operator delete[](void* ptr, size_t) noexcept {
    solarpunk::MemoryManager::instance().free(ptr);
}
