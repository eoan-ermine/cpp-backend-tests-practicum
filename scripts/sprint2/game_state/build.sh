#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/game_state/solution

docker build -t game_state ${SOLUTION_FOLDER}
