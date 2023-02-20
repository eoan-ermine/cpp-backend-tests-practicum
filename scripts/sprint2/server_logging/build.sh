#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/server_logging/solution

docker build -t server_logging ${SOLUTION_FOLDER}
