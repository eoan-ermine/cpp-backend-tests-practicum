#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/time_control/solution

docker build -t time_control ${SOLUTION_FOLDER}