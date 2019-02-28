#!/usr/bin/env bash

set -eux

echo $PWD

cd ../connection

INVENTORY=../connection_aws_ssm/inventory.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    "$@"
