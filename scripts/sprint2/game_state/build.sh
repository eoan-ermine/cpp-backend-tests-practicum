#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/game_state
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/game_state/solution

docker build -t game_state ${SOLUTION_FOLDER}
