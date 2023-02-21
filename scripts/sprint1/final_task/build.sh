#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/final_task
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/final_task/solution

cd ${SOLUTION_FOLDER} || exit 1

docker build -t final_task .
