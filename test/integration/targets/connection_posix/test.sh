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
