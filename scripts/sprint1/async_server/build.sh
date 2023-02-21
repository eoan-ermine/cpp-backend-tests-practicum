#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/async_server
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/async_server/solution

cd ${SOLUTION_FOLDER} || exit 1
mkdir -p build
cd build
conan install ..
cmake -D CMAKE_CXX_COMPILER=/usr/bin/g++-11 ..
cmake --build . -j $(nproc)
