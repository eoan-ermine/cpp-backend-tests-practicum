#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/restaurant_multi_threaded/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/restaurant_multi_threaded

bash ${SCRIPT_FOLDER}/build.sh

${SOLUTION_FOLDER}/build/bin/restaurant
