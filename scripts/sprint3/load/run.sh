#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/load/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/load

bash ${SCRIPT_FOLDER}/build.sh

export DIRECTORY=/solution/logs


docker run --rm -e DIRECTORY=${DIRECTORY} load

rm -r ${SCRIPT_FOLDER}/solution ${SCRIPT_FOLDER}/test_s03_load.py