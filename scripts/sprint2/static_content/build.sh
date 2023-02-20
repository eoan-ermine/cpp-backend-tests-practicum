#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/static_content/solution

cd ${SOLUTION_FOLDER} || exit 1

mkdir -p build
cd build
conan install ..
cmake ..
cmake --build . -j $(nproc)
