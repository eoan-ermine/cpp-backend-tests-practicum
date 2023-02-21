#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/scores
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/scores/solution

docker build -t scores ${SOLUTION_FOLDER}
