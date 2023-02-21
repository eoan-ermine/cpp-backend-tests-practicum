#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/server_logging
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/server_logging/solution

docker build -t server_logging ${SOLUTION_FOLDER}
