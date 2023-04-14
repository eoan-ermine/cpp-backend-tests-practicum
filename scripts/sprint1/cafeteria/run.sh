#!/bin/bash

function real_dir() {
  pushd "$1" >/dev/null
  pwd -P
  popd >/dev/null
}
SCRIPT_FOLDER=$(real_dir "$(dirname "$0")")

BASE_DIR=${SCRIPT_FOLDER}/../../../../
SOLUTION_FOLDER=${BASE_DIR}/sprint1/problems/cafeteria/solution

bash ${SCRIPT_FOLDER}/build.sh || exit 1
source ${BASE_DIR}/.venv/bin/activate

${SOLUTION_FOLDER}/build/bin/cafeteria
