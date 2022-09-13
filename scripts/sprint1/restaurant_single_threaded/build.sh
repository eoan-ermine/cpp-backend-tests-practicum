#!/bin/bash

cd sprint1/problems/restaurant_single_threaded/solution
mkdir -p build
cd build
conan install ..
cmake -D CMAKE_CXX_COMPILER=/usr/bin/g++-11 ..
cmake --build .
