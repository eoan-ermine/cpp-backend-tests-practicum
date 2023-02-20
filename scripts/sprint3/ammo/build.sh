#!/bin/bash


BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/ammo/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/ammo

cp ${BASE_DIR}/cpp-backend-tests-practicum/tests/test_s03_ammo.py ${SCRIPT_FOLDER}/test_s03_ammo.py
cp -r ${SOLUTION_FOLDER} ${SCRIPT_FOLDER}/solution

docker build -t ammo ${SCRIPT_FOLDER}