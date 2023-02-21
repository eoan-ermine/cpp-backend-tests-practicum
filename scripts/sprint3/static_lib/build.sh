#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/static_lib
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/static_lib/solution

docker build -t static_lib ${SOLUTION_FOLDER}
