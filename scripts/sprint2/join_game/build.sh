#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint2/join_game
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/join_game/solution

docker build -t join_game ${SOLUTION_FOLDER}