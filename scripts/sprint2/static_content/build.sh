#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/static_content
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/static_content/solution

cd ${SOLUTION_FOLDER} || exit 1

mkdir -p build
cd build
conan install ..
cmake ..
cmake --build . -j $(nproc)
