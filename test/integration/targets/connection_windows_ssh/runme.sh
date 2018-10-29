#!/usr/bin/env bash

set -eux

# sftp
./windows.sh "$@"
# scp
ANSIBLE_SCP_IF_SSH=true ./windows.sh "$@"

ansible-playbook -i ../../inventory.winrm -i test_connection.inventory tests.yml \
    "$@"
