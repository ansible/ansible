#!/usr/bin/env bash

set -eux

cd ../connection

INVENTORY=~/ansible_testing/test_connection.inventory ./test.sh \
    -e target_hosts=windows-ssh \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "$@"

cd ../connection_windows_ssh
