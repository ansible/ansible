#!/usr/bin/env bash

set -eux

cd ../connection

INVENTORY=../connection_posix/test_connection.inventory ./test.sh \
    -e hosts=all \
    -e action_prefix= \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    "$@"

