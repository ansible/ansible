#!/usr/bin/env bash

set -eux

# Connection tests for POSIX platforms use this script by linking to it from the appropriate 'connection_' target dir.
# The name of the inventory group to test is extracted from the directory name following the 'connection_' prefix.

group=$(python -c \
    "from os import path; print(path.basename(path.abspath(path.dirname('$0'))).replace('connection_', ''))")

cd ../connection

INVENTORY="../connection_${group}/test_connection.inventory" ./test.sh \
    -e target_hosts="${group}" \
    -e action_prefix= \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    "$@"

DOCKER_VERSION=$(docker version -f '{{ .Client.Version }}')
CWD=/var/tmp

if ansible all -i localhost, -m assert -a"that={{ docker_version is version('17.09', '>=') }}" -e docker_version=$DOCKER_VERSION; then
    OLD_DOCKER=false
else
    OLD_DOCKER=true
fi

ansible-playbook test_workdir.yml -i test_connection.inventory -e ansible_docker_cwd=$CWD -e old_docker=$OLD_DOCKER
