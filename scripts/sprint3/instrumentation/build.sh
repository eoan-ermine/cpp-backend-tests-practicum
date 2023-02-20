#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/instrumentation/solution

cd ${SOLUTION_FOLDER} || exit 1
g++ -O3 *.cpp -o event2dot
