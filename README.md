# CIS-277 Assignment 1: Network Packet Buffer Pool

## Student

Sean Park

## Description

The pool has eight 512-byte blocks. A stack holds the free addresses. `allocate()` pops one. `deallocate()` pushes it back if the pointer is valid and not already free. `main.cpp` writes a packet, reads it back, reuses a freed block, then shows a full pool and a double free.

## Stack Implementation

Dynamic Array

Stack stores items in a vector. `push` adds to the end. `pop` and `top` use the last item. The array can grow. It is not a fixed array, a linked list, or `std::stack`.

## How to Compile

```bash
g++ -std=c++17 -Wall -Wextra -pedantic main.cpp MemoryPool.cpp -o buffer_pool
```

## How to Run

```bash
./buffer_pool
```

## Analysis Questions

1. Why is a Stack appropriate for managing the free blocks in this memory pool?

    All free blocks are the same size. You only need the next address, so `push` and `pop` are enough.

2. What happens when the free-block Stack becomes empty?

    `allocate()` returns `nullptr`. The pool is full.

3. Why must a released block be returned to the Stack?

    `allocate()` only takes blocks from the stack. If a freed block is not pushed back, it can never be reused.

4. What problem could occur if the same block were deallocated twice?

    The same address would be on the stack twice. Two later allocations could get the same block and overwrite each other.

5. What is the Big-O time complexity of `allocate()`? Explain why.

    `O(1)`. It pops one pointer. It does not loop over the blocks.

6. What is the Big-O time complexity of `deallocate()`? Explain why.

    `O(1)`. It checks the pointer, then pushes it. It does not loop over the blocks.
