#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint4/bookypedia-1
SOLUTION_FOLDER=${BASE_DIR}/sprint4/problems/bookypedia-1/solution

cd ${SOLUTION_FOLDER} || exit 1
mkdir build
cd build
conan install .. --build=missing -s compiler.libcxx=libstdc++11 -s build_type=Release
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j $(nproc)