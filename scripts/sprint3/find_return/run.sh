#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/find_return/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/find_return

bash ${SCRIPT_FOLDER}/build.sh

export CONFIG_PATH=${SOLUTION_FOLDER}/data/config.json

export IMAGE_NAME=find_return
export ENTRYPOINT=/app/game_server
export CONTAINER_ARGS='--config-file /app/data/config.json --www-root /app/static/'

pytest --workers auto --junitxml=${BASE_DIR}/find_return.xml cpp-backend-tests-practicum/tests/test_s03_find_return.py
