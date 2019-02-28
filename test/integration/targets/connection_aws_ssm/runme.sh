#!/usr/bin/env bash

set -eux

cd ../connection

INVENTORY=../../inventory.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    "$@"
