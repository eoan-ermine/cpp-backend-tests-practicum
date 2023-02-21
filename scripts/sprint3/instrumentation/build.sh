#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/instrumentation
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/instrumentation/solution

cd ${SOLUTION_FOLDER} || exit 1
g++ -O3 *.cpp -o event2dot
