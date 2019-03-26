#!/usr/bin/env bash

set -eux

CMD_ARGS=("$@")

# Destroy Environment
cleanup() {

    cd ../connection_aws_ssm

    ansible-playbook -c local aws_ssm_integration_test_teardown.yml "${CMD_ARGS[@]}"

}

trap "cleanup" EXIT

# Setup Environment
ansible-playbook -c local aws_ssm_integration_test_setup.yml "$@"

# Export the AWS Keys
set +x
. ./aws-env-vars.sh
set -x

cd ../connection

# Execute Integration tests for Linux
INVENTORY=../connection_aws_ssm/inventory-linux.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    -e action_prefix= \
    "$@"

# Execute Integration tests for Windows
INVENTORY=../connection_aws_ssm/inventory-windows.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    -e action_prefix=win_ \
    "$@"
