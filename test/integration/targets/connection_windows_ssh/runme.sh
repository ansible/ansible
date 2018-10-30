#!/usr/bin/env bash

set -eux

# template out the inventory file that's based on the current Windows host details
ansible -i ../../inventory.winrm localhost \
    -m template \
    -a "src=test_connection.inventory.j2 dest=test_connection.inventory" \
    "$@"

# sftp
./windows.sh "$@"
# scp - until https://github.com/PowerShell/Win32-OpenSSH/issues/1284 is resolved
# ANSIBLE_SCP_IF_SSH=true ./windows.sh "$@"

ansible-playbook -i test_connection.inventory tests.yml \
    "$@"

rm test_connection.inventory
