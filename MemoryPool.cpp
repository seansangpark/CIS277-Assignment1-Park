#include "MemoryPool.h"

MemoryPool::MemoryPool(size_t blockSize, size_t blockCount)
{
    bytesPerBlock = blockSize;
    numBlocks = blockCount;
    memory = nullptr;
    used = nullptr;

    if (bytesPerBlock == 0 || numBlocks == 0)
    {
        return;
    }

    memory = new unsigned char[bytesPerBlock * numBlocks];
    used = new bool[numBlocks];

    for (size_t i = 0; i < numBlocks; i++)
    {
        used[i] = false;
        freeBlocks.push(memory + (i * bytesPerBlock));
    }
}

MemoryPool::~MemoryPool()
{
    delete[] memory;
    delete[] used;
}

void* MemoryPool::allocate()
{
    if (freeBlocks.empty())
    {
        return nullptr;
    }

    void* block = freeBlocks.pop();

    size_t index = 0;
    findBlock(block, index);
    used[index] = true;

    return block;
}

bool MemoryPool::deallocate(void* ptr)
{
    size_t index = 0;
    if (!findBlock(ptr, index))
    {
        return false;
    }

    if (!used[index])
    {
        return false;
    }

    used[index] = false;
    freeBlocks.push(ptr);
    return true;
}

size_t MemoryPool::availableBlocks() const
{
    return freeBlocks.size();
}

size_t MemoryPool::allocatedBlocks() const
{
    return numBlocks - freeBlocks.size();
}

size_t MemoryPool::blockSize() const
{
    return bytesPerBlock;
}

size_t MemoryPool::capacity() const
{
    return bytesPerBlock * numBlocks;
}

bool MemoryPool::findBlock(void* ptr, size_t& index) const
{
    if (ptr == nullptr || memory == nullptr || bytesPerBlock == 0)
    {
        return false;
    }

    unsigned char* block = static_cast<unsigned char*>(ptr);
    if (block < memory)
    {
        return false;
    }

    size_t offset = static_cast<size_t>(block - memory);
    if (offset % bytesPerBlock != 0)
    {
        return false;
    }

    index = offset / bytesPerBlock;
    return index < numBlocks;
}
