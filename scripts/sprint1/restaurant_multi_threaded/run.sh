#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/restaurant_multi_threaded
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/restaurant_multi_threaded/solution

bash ${SCRIPT_FOLDER}/build.sh

${SOLUTION_FOLDER}/build/bin/restaurant
