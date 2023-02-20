#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/instrumentation/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/instrumentation

bash ${SCRIPT_FOLDER}/build.sh

export REPORT_PATH=${SOLUTION_FOLDER}/report
export BINARY_PATH=${SOLUTION_FOLDER}/event2dot
export ARG=${SOLUTION_FOLDER}/inputs

pytest --junitxml=${BASE_DIR}/instrumentation.xml cpp-backend-tests-practicum/tests/test_s03_instrumentation.py
