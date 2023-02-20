#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/move_players/solution

docker build -t move_players ${SOLUTION_FOLDER}
