#ifndef STACK_H
#define STACK_H

#include <cstddef>
#include <vector>

template <typename T>
class Stack
{
public:
    void push(const T& value)
    {
        data.push_back(value);
    }

    T pop()
    {
        T value = data.back();
        data.pop_back();
        return value;
    }

    T& top()
    {
        return data.back();
    }

    bool empty() const
    {
        return data.empty();
    }

    size_t size() const
    {
        return data.size();
    }

private:
    std::vector<T> data;
};

#endif
