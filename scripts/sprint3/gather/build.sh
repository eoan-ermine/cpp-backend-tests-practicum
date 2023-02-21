#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/gather
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/gather/solution
CPP_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/tests/cpp/test_s03_gather

cp -r ${CPP_FOLDER}/* ${SOLUTION_FOLDER}/src/
docker build -t gather . ${SOLUTION_FOLDER}
