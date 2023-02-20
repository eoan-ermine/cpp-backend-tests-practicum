#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/logger/solution

cd ${SOLUTION_FOLDER} || exit 1

cp cpp-backend-tests-practicum/tests/cpp/test_s02_logger/main.cpp ${SOLUTION_FOLDER}

mkdir -p build
cd build
conan install ..
cmake ..
cmake --build . -j $(nproc)
