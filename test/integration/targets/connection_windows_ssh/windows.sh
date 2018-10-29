#!/usr/bin/env bash

set -eux

cd ../connection

INVENTORY=../../inventory.winrm ./test.sh \
    -i ../connection_windows_ssh/test_connection.inventory \
    -e target_hosts=winrm \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "$@"

cd ../connection_windows_ssh
