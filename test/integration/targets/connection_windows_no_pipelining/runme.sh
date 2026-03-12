#!/usr/bin/env bash

set -eux

export ANSIBLE_CONNECTION_PLUGINS="${PWD}/connection_plugins"

# make sure hosts are using our custom winrm connection that disables pipelining
ansible -i ../../inventory.winrm localhost \
    -m template \
    -a "src=test_connection.inventory.j2 dest=${OUTPUT_DIR}/test_connection.inventory" \
    "$@"

TEST_PLAYBOOK="${PWD}/tests.yml"

cd ../connection

INVENTORY="${OUTPUT_DIR}/test_connection.inventory" ./test.sh \
    -e target_hosts=windows \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "$@"

cd ../connection_windows_no_pipelining

ansible-playbook -i "${OUTPUT_DIR}/test_connection.inventory" "${TEST_PLAYBOOK}" \
    "$@"
