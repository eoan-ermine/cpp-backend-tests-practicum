#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint1/map_json
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/map_json/solution

bash ${SCRIPT_FOLDER}/build.sh

source ${BASE_DIR}/.venv/bin/activate

export DELIVERY_APP=${SOLUTION_FOLDER}/build/bin/game_server
export CONFIG_PATH=${SOLUTION_FOLDER}/data/config.json
export COMMAND_RUN="${DELIVERY_APP} ${CONFIG_PATH}"

python3 -m pytest --rootdir=${BASE_DIR} --verbose --junitxml=results.xml cpp-backend-tests-practicum/tests/test_l04_map_json.py
