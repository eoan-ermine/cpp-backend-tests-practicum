#!/bin/bash

function real_dir() {
  pushd "$1" >/dev/null
  pwd -P
  popd >/dev/null
}

SCRIPT_FOLDER=$(real_dir "$(dirname "$0")")
BASE_DIR=${SCRIPT_FOLDER}/../../../../
SOLUTION_FOLDER=${BASE_DIR}/sprint3/problems/ammo/solution

NETWORK_NAME=ammo_network

docker network rm ${NETWORK_NAME}
docker network create ${NETWORK_NAME}

echo $(docker run --rm -d --network=${NETWORK_NAME} --name=cpp_server praktikumcpp/game_server:latest)

bash ${SCRIPT_FOLDER}/build.sh

export DIRECTORY=/solution/logs

docker run --rm --privileged --network=${NETWORK_NAME} -e DIRECTORY=${DIRECTORY} ammo

docker container stop cpp_server
docker network rm ${NETWORK_NAME}

rm -r ${SCRIPT_FOLDER}/solution ${SCRIPT_FOLDER}/test_s03_ammo.py