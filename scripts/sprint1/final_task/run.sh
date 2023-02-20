#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/final_task/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/final_task

bash ${SCRIPT_FOLDER}/build.sh

export IMAGE_NAME=final_task
python3 -m pytest --workers=auto --rootdir=${BASE_DIR} --verbose --junitxml=results.xml cpp-backend-tests-practicum/tests/test_l05_final_task.py
