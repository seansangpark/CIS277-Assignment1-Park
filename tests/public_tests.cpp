// Public CIS-277 Assignment 1 checks. No student implementation is supplied.
// These exercise only the published interfaces and positive-size pool behavior.
#include "Stack.h"
#include "MemoryPool.h"

#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <type_traits>
#include <utility>
#include <vector>

// Member-pointer conversion permits overloads/additional members while checking
// the specified parameter, return, and const signatures. Never construct Stack.
template<class T> struct StackContract {
    using S = Stack<T>;
    static_assert(std::is_same_v<decltype(static_cast<void (S::*)(const T&)>(&S::push)), void (S::*)(const T&)>, "Stack::push must accept const T& and return void");
    static_assert(std::is_same_v<decltype(static_cast<T (S::*)()>(&S::pop)), T (S::*)()>, "Stack::pop must return T");
    static_assert(std::is_same_v<decltype(static_cast<T& (S::*)()>(&S::top)), T& (S::*)()>, "Stack::top must return T&");
    static_assert(std::is_same_v<decltype(static_cast<bool (S::*)() const>(&S::empty)), bool (S::*)() const>, "Stack::empty must be const and return bool");
    static_assert(std::is_same_v<decltype(static_cast<std::size_t (S::*)() const>(&S::size)), std::size_t (S::*)() const>, "Stack::size must be const and return size_t");
};
static_assert(sizeof(StackContract<int>) > 0);
static_assert(sizeof(StackContract<void*>) > 0);
static_assert(std::is_constructible_v<MemoryPool, std::size_t, std::size_t>, "MemoryPool must accept block size and block count");
static_assert(std::is_destructible_v<MemoryPool>, "MemoryPool must be destructible");
static_assert(std::is_same_v<decltype(static_cast<void* (MemoryPool::*)()>(&MemoryPool::allocate)), void* (MemoryPool::*)()>, "allocate must return void*");
static_assert(std::is_same_v<decltype(static_cast<bool (MemoryPool::*)(void*)>(&MemoryPool::deallocate)), bool (MemoryPool::*)(void*)>, "deallocate must accept void* and return bool");
static_assert(std::is_same_v<decltype(static_cast<std::size_t (MemoryPool::*)() const>(&MemoryPool::availableBlocks)), std::size_t (MemoryPool::*)() const>, "availableBlocks must be const and return size_t");
static_assert(std::is_same_v<decltype(static_cast<std::size_t (MemoryPool::*)() const>(&MemoryPool::allocatedBlocks)), std::size_t (MemoryPool::*)() const>, "allocatedBlocks must be const and return size_t");
static_assert(std::is_same_v<decltype(static_cast<std::size_t (MemoryPool::*)() const>(&MemoryPool::blockSize)), std::size_t (MemoryPool::*)() const>, "blockSize must be const and return size_t");
static_assert(std::is_same_v<decltype(static_cast<std::size_t (MemoryPool::*)() const>(&MemoryPool::capacity)), std::size_t (MemoryPool::*)() const>, "capacity must be const and return size_t");

void require(bool condition, const char* check) {
    if (!condition) {
        std::cerr << "FAIL: " << check << " (expected true, actual false)\n";
        std::exit(1);
    }
}

void equal_count(std::size_t actual, std::size_t expected, const char* check) {
    if (actual != expected) {
        std::cerr << "FAIL: " << check << " (expected " << expected << ", actual " << actual << ")\n";
        std::exit(1);
    }
}

void counts(const MemoryPool& pool, std::size_t available, std::size_t allocated) {
    equal_count(pool.availableBlocks(), available, "availableBlocks");
    equal_count(pool.allocatedBlocks(), allocated, "allocatedBlocks");
}

unsigned char payload(std::size_t block, std::size_t offset) {
    // Include zero and high-bit bytes in every full-block pattern.
    return offset == 0 ? 0 : offset == 1 ? 0xff : static_cast<unsigned char>((block * 53 + offset * 97) & 255);
}

void exercise_pool(std::size_t bytes, std::size_t count) {
    MemoryPool pool(bytes, count);
    counts(pool, count, 0);
    equal_count(pool.blockSize(), bytes, "blockSize");
    equal_count(pool.capacity(), bytes * count, "capacity in bytes");
    std::vector<void*> blocks;
    for (std::size_t i = 0; i < count; ++i) {
        void* block = pool.allocate();
        require(block != nullptr, "allocation before exhaustion");
        for (void* existing : blocks) require(block != existing, "distinct live allocations");
        blocks.push_back(block);
        counts(pool, count - i - 1, i + 1);
        auto* data = static_cast<unsigned char*>(block);
        for (std::size_t j = 0; j < bytes; ++j) data[j] = payload(i, j);
    }
    for (int repeat = 0; repeat < 3; ++repeat) {
        require(pool.allocate() == nullptr, "repeated nullptr exhaustion");
        counts(pool, 0, count);
    }
    for (std::size_t i = 0; i < count; ++i) {
        const auto* data = static_cast<const unsigned char*>(blocks[i]);
        for (std::size_t j = 0; j < bytes; ++j)
            equal_count(data[j], payload(i, j), "full-block binary readback/isolation");
    }

    int foreign = 0;
    MemoryPool other(bytes, 1);
    void* other_block = other.allocate();
    require(other_block != nullptr, "other-pool allocation");
    void* invalid[] = {nullptr, &foreign, other_block, static_cast<unsigned char*>(blocks[0]) + 1};
    for (void* pointer : invalid) {
        require(!pool.deallocate(pointer), "reject null/foreign/other-pool/interior release");
        counts(pool, 0, count);
        require(pool.allocate() == nullptr, "invalid release must not add reusable blocks");
    }
    require(other.deallocate(other_block), "other pool retains its own allocation");
    counts(other, 1, 0);

    require(pool.deallocate(blocks[0]), "release live block");
    counts(pool, 1, count - 1);
    require(!pool.deallocate(blocks[0]), "reject duplicate release");
    counts(pool, 1, count - 1);
    require(pool.allocate() == blocks[0], "duplicate rejection preserves reusable block");
    counts(pool, 0, count);
    require(pool.allocate() == nullptr, "duplicate release must not add extra blocks");

    for (std::size_t i = 0; i < count; ++i) {
        require(pool.deallocate(blocks[i]), "release for LIFO reuse");
        counts(pool, i + 1, count - i - 1);
    }
    for (std::size_t i = 0; i < count; ++i) {
        void* reused = pool.allocate();
        require(reused == blocks[count - i - 1], "LIFO reuse after release");
        counts(pool, count - i - 1, i + 1);
    }
    // All blocks intentionally remain allocated: destruction must reclaim them.
}

int main() {
    exercise_pool(7, 1);
    exercise_pool(17, 4);
    for (int lifetime = 0; lifetime < 12; ++lifetime) exercise_pool(9, 3);
    std::cout << "PASS: Public pool interface, state, binary isolation, release, reuse, and lifetime checks passed.\n";
    return 0;
}
