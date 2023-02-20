#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/static_lib/solution

docker build -t static_lib ${SOLUTION_FOLDER}
