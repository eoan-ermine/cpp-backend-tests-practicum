#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/async_server/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/async_server

bash ${SCRIPT_FOLDER}/build.sh

source ${BASE_DIR}/.venv/bin/activate
export COMMAND_RUN=${SOLUTION_FOLDER}/build/bin/hello_async

python3 -m pytest --rootdir=${BASE_DIR} --verbose --junitxml=results.xml cpp-backend-tests-practicum/tests/test_l03_hello_async.py
