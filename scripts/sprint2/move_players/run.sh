#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/move_players
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/move_players/solution

bash ${SCRIPT_FOLDER}/build.sh

export CONFIG_PATH=${SOLUTION_FOLDER}/data/config.json
export IMAGE_NAME=move_players

pytest --workers auto --junitxml=${BASE_DIR}/move_players.xml cpp-backend-tests-practicum/tests/test_s02_move_players.py