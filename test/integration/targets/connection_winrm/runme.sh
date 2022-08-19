#!/usr/bin/env bash

set -eux

for INV in test_connection.inventory.j2 test_fqcn_connection.inventory.j2; do
# make sure hosts are using winrm connections
ansible -i ../../inventory.winrm localhost \
    -m template \
    -a "src=$INV dest=${OUTPUT_DIR}/test_connection.inventory" \
    "$@"

cd ../connection

INVENTORY="${OUTPUT_DIR}/test_connection.inventory" ./test.sh \
    -e target_hosts=windows \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "$@"

cd ../connection_winrm

ansible-playbook -i "${OUTPUT_DIR}/test_connection.inventory" tests.yml \
    "$@"
done
