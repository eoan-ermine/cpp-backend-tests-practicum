#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/scores/solution

docker build -t scores ${SOLUTION_FOLDER}
