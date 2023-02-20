#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint4/problems/state_serialization/solution
VOLUME_DIR=${SOLUTION_FOLDER}/../volume

docker build -t state_serialization ${SOLUTION_FOLDER}

mkdir -p ${VOLUME_DIR}
chmod 777 ${VOLUME_DIR}
