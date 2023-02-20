#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/static_content/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/static_content

bash ${SCRIPT_FOLDER}/build.sh

export CONFIG_PATH=${SOLUTION_FOLDER}/data/config.json

export DELIVERY_APP=${SOLUTION_FOLDER}/build/bin/game_server
export DATA_PATH=${SOLUTION_FOLDER}/static/

export COMMAND_RUN="${DELIVERY_APP} ${CONFIG_PATH} ${DATA_PATH}"

python3 -m pytest --rootdir=${BASE_DIR} --verbose --junitxml=results.xml cpp-backend-tests-practicum/tests/test_s02_static_content.py
