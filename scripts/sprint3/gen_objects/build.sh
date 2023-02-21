#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/gen_objects
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/gen_objects/solution

docker build -t gen_objects ${SOLUTION_FOLDER}
