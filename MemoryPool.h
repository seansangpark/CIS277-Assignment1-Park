#ifndef MEMORY_POOL_H
#define MEMORY_POOL_H

#include "Stack.h"
#include <cstddef>

class MemoryPool
{
public:
    MemoryPool(size_t blockSize, size_t blockCount);
    ~MemoryPool();

    MemoryPool(const MemoryPool&) = delete;
    MemoryPool& operator=(const MemoryPool&) = delete;

    void* allocate();
    bool deallocate(void* ptr);

    size_t availableBlocks() const;
    size_t allocatedBlocks() const;
    size_t blockSize() const;
    size_t capacity() const;

private:
    bool findBlock(void* ptr, size_t& index) const;

    unsigned char* memory;
    bool* used;
    size_t bytesPerBlock;
    size_t numBlocks;
    Stack<void*> freeBlocks;
};

#endif
