#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/gather-tests_wrong2
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/gather-tests/solution
CPP_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/tests/cpp/test_s03_gather-tests

cp -r ${CPP_FOLDER}/* ${SOLUTION_FOLDER}/src/
cp ${CPP_FOLDER}/wrong/collision_detector.cpp ${SOLUTION_FOLDER}/src/
cp ${CPP_FOLDER}/wrong/CMakeLists.txt ${SOLUTION_FOLDER}/
cp ${CPP_FOLDER}/wrong/Dockerfile2 ${SOLUTION_FOLDER}/Dockerfile

docker build -t gather-tests_wrong2 ${SOLUTION_FOLDER}