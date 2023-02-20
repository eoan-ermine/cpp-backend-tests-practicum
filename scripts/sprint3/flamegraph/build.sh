#!/bin/bash

BASE_DIR=${PWD}
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/flamegraph/solution
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint3/flamegraph

MAP_JSON_FOLDER=${BASE_DIR}/sprint1/problems/map_json/solution
MAP_JSON_CONFIG=${MAP_JSON_FOLDER}/data/config.json
MAP_JSON_PROGRAM=${MAP_JSON_FOLDER}/build/bin/game_server

cd ${SOLUTION_FOLDER} || exit 1

FOLDER=FlameGraph
if [ ! -d "${FOLDER}" ] ; then
  git clone https://github.com/brendangregg/FlameGraph
else
  (
  cd "${FOLDER}" || exit 1
  git pull
  )
fi

chmod +x ${MAP_JSON_PROGRAM}
