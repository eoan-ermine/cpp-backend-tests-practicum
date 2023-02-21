#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint4/state_serialization
SOLUTION_FOLDER=${BASE_DIR}/sprint4/problems/state_serialization/solution
VOLUME_DIR=${BASE_DIR}/sprint4/problems/state_serialization/volume

bash ${SCRIPT_FOLDER}/build.sh

export CONFIG_PATH=${SOLUTION_FOLDER}/data/config.json

export VOLUME_PATH=${VOLUME_DIR}
export IMAGE_NAME=state_serialization

pytest --junitxml=${BASE_DIR}/state_serialization.xml cpp-backend-tests-practicum/tests/test_s04_state_serialization.py
