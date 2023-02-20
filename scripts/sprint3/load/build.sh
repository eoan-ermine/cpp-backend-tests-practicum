#!/bin/bash


BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/load/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/load

cp ${BASE_DIR}/cpp-backend-tests-practicum/tests/test_s03_ammo.py ${SCRIPT_FOLDER}/test_s03_load.py
cp -r ${SOLUTION_FOLDER} ${SCRIPT_FOLDER}/solution

docker build -t load ${SCRIPT_FOLDER}