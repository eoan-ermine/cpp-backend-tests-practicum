#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint4/problems/db_of_books/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint4/db_of_books

cd ${SOLUTION_FOLDER} || exit 1
mkdir -p build
cd build
conan install ..
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j $(nproc)