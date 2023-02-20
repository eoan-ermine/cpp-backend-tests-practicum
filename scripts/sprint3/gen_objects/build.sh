#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/gen_objects/solution

docker build -t gen_objects ${SOLUTION_FOLDER}
