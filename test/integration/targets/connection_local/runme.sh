#!/usr/bin/env bash

set -eux

group=local

pushd ../connection

INVENTORY="../connection_${group}/test_connection.inventory" ./test.sh \
    -e target_hosts="${group}" \
    -e action_prefix= \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    "$@"

ANSIBLE_CONNECTION_PLUGINS="../connection_${group}/connection_plugins" INVENTORY="../connection_${group}/test_network_connection.inventory" ./test.sh \
    -e target_hosts="${group}" \
    -e action_prefix= \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    "$@"

popd

ANSIBLE_ROLES_PATH=../ ansible-playbook -i ../../inventory test_become_password_handling.yml "$@"
