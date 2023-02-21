#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/time_control
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/time_control/solution

docker build -t time_control ${SOLUTION_FOLDER}