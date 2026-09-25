#include "MemoryPool.h"
#include <cstring>
#include <iostream>
using namespace std;

int main()
{
    const size_t kBlockSize = 512;
    const size_t kBlockCount = 8;

    MemoryPool pool(kBlockSize, kBlockCount);

    cout << "Network Packet Buffer Pool" << endl << endl;
    cout << "Block Size:       " << pool.blockSize() << " bytes" << endl;
    cout << "Blocks:           " << kBlockCount << endl;
    cout << "Total Capacity:   " << pool.capacity() << " bytes" << endl << endl;

    void* packet1 = pool.allocate();
    void* packet2 = pool.allocate();
    void* packet3 = pool.allocate();

    cout << "Packet 1 allocated: " << packet1 << endl;
    cout << "Packet 2 allocated: " << packet2 << endl;
    cout << "Packet 3 allocated: " << packet3 << endl << endl;

    cout << "Available blocks: " << pool.availableBlocks() << endl;
    cout << "Allocated blocks: " << pool.allocatedBlocks() << endl << endl;

    unsigned char data[] = {0x45, 0x00, 0x00, 0x3C, 0xAB, 0xCD, 0x12, 0x34};
    memcpy(packet1, data, sizeof(data));

    unsigned char copy[8];
    memcpy(copy, packet1, sizeof(copy));

    cout << "Binary packet written to Packet 1." << endl;
    cout << "Read back:";
    cout << hex;
    for (size_t i = 0; i < sizeof(copy); i++)
    {
        cout << " 0x" << (int)copy[i];
    }
    cout << dec << endl << endl;

    pool.deallocate(packet2);
    cout << "Packet 2 released." << endl << endl;

    cout << "Available blocks: " << pool.availableBlocks() << endl;
    cout << "Allocated blocks: " << pool.allocatedBlocks() << endl << endl;

    void* packet4 = pool.allocate();
    cout << "Packet 4 allocated: " << packet4 << endl;

    if (packet4 == packet2)
    {
        cout << "Packet 4 reused the previously released block." << endl << endl;
    }

    cout << "Attempting to exhaust pool..." << endl;
    while (pool.allocate() != nullptr)
    {
    }

    void* failed = pool.allocate();
    if (failed == nullptr)
    {
        cout << "No blocks available." << endl;
        cout << "allocate() returned nullptr." << endl << endl;
    }

    cout << "Available blocks: " << pool.availableBlocks() << endl;
    cout << "Allocated blocks: " << pool.allocatedBlocks() << endl << endl;

    cout << "Attempting double deallocation..." << endl;
    pool.deallocate(packet1);
    if (!pool.deallocate(packet1))
    {
        cout << "Double deallocation rejected." << endl;
    }

    return 0;
}
