#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/find_return/solution

docker build -t find_return ${SOLUTION_FOLDER}