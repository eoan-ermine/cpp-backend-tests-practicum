#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/gather/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/gather

bash ${SCRIPT_FOLDER}/build.sh

docker run --rm --entrypoint /app/build/collision_detection_tests gather