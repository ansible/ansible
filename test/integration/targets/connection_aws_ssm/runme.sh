#!/usr/bin/env bash

# Setup Environment
ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml \
    --tags setup_infra \
    "$@"

# Execute test cases only on Python 2.7
if [ -e aws-env-vars.sh ]; then

    # Export the AWS Keys
    . ./aws-env-vars.sh

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

    cd ../connection_aws_ssm

    # Destroy Environment
    ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml \
        --tags delete_infra \
        "$@"
fi
