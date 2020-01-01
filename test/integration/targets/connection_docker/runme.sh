#!/usr/bin/env bash

DOCKER_CONTAINERS="docker-connection-test-container"

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

echo "Setup"
ANSIBLE_ROLES_PATH=.. ansible-playbook setup.yml

cleanup() {
    echo "Cleanup"
    docker rm -f ${DOCKER_CONTAINERS}
    echo "Done"
    exit 0
}

trap cleanup INT TERM EXIT

echo "Start containers"
for CONTAINER in ${DOCKER_CONTAINERS}; do
    docker run --rm --name ${CONTAINER} --detach python:3 /bin/sh -c 'sleep 10m'
    echo ${CONTAINER}
done

echo "Run tests"
./runme-connection.sh
