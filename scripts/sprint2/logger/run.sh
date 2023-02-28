#!/bin/bash

function real_dir() {
  pushd "$1" >/dev/null
  pwd -P
  popd >/dev/null
}
SCRIPT_FOLDER=$(real_dir "$(dirname "$0")")

BASE_DIR=${SCRIPT_FOLDER}/../../../..
SOLUTION_FOLDER=${BASE_DIR}/sprint2/problems/logger/solution

bash ${SCRIPT_FOLDER}/build.sh

cd ${BASE_DIR}
sudo ${SOLUTION_FOLDER}/build/bin/hello_log