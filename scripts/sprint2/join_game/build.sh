#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/join_game/solution

docker build -t join_game ${SOLUTION_FOLDER}