#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/move_players
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/move_players/solution

docker build -t move_players ${SOLUTION_FOLDER}
