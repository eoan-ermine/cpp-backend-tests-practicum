#!/bin/bash

REPO=${PWD}

source ${REPO}/.venv/bin/activate

export COMMAND_RUN="docker run --rm -p 8080:8080 my_http_server"

python3 -m pytest --rootdir=${REPO} --verbose --junitxml=results.xml cpp-backend-tests-practicum/tests/test_l05_final_task.py
