#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/logger
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/logger/solution

bash ${SCRIPT_FOLDER}/build.sh

source ${REPO}/.venv/bin/activate

${SOLUTION_FOLDER}/build/bin/hello_log