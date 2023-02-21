#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/server_logging
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/server_logging/solution

bash ${SCRIPT_FOLDER}/build.sh

export CONFIG_PATH=${SOLUTION_FOLDER}/data/config.json
export IMAGE_NAME=server_logging

pytest --workers auto --junitxml=${BASE_DIR}/server_logging.xml cpp-backend-tests-practicum/tests/test_s02_server_logging.py
