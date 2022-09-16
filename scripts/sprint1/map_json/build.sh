#!/bin/bash

cd sprint1/problems/map_json/solution
mkdir -p build
cd build
conan install ..
cmake -D CMAKE_CXX_COMPILER=/usr/bin/g++-11 ..
cmake --build .
