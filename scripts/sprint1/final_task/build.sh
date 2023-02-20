#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/final_task/solution

cd ${SOLUTION_FOLDER} || exit 1

docker build -t final_task .
