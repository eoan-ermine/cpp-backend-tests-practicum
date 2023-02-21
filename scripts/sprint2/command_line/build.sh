#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/command_line
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/command_line/solution

docker build -t command_line ${SOLUTION_FOLDER}
