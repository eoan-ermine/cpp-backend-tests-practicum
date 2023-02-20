#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/command_line/solution

docker build -t command_line ${SOLUTION_FOLDER}
