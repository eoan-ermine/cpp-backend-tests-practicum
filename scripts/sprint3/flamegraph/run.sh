#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/flamegraph/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/flamegraph

MAP_JSON_FOLDER=${BASE_DIR}/sprint1/problems/map_json/solution
MAP_JSON_CONFIG=${MAP_JSON_FOLDER}/data/config.json
MAP_JSON_PROGRAM=${MAP_JSON_FOLDER}/build/bin/game_server

bash ${SCRIPT_FOLDER}/build.sh

cd ${SOLUTION_FOLDER} || exit 1

export DIRECTORY=${SOLUTION_FOLDER}

sudo python3 shoot.py "${MAP_JSON_PROGRAM} ${MAP_JSON_CONFIG}"

sudo chown -R runner:docker ${SOLUTION_FOLDER}
ls -l
pytest --junitxml=${BASE_DIR}/flamegraph.xml ${BASE_DIR}/cpp-backend-tests-practicum/tests/test_s03_flamegraph.py

chmod +x ${MAP_JSON_PROGRAM}
