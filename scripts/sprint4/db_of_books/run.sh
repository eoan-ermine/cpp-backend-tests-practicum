#!/bin/bash

BASE_DIR=${PWD}
SCRIPT_FOLDER=${BASE_DIR}/cpp-backend-tests-practicum/scripts/sprint4/db_of_books
SOLUTION_FOLDER=${BASE_DIR}/sprint4/problems/db_of_books/solution
GET_IP=${SCRIPT_FOLDER}/../get_ip.py

bash $SCRIPT_FOLDER/build.sh

docker container stop postgres && docker container rm postgres

POSTGRES_ID=$(docker run --name postgres -e POSTGRES_HOST_AUTH_METHOD=trust -d --rm postgres)

sleep 5s # wait while postgres is setting up

export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=Mys3Cr3t
export POSTGRES_HOST=$(python3 ${GET_IP} $POSTGRES_ID)
export POSTGRES_PORT=5432
export DELIVERY_APP=${SOLUTION_FOLDER}/build/book_manager

pytest --junitxml=${BASE_DIR}/db_of_books.xml ${BASE_DIR}/cpp-backend-tests-practicum/tests/test_s04_db_of_books.py

docker container stop postgres
docker container stop postgres
