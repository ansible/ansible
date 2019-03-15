#!/usr/bin/env bash
set -eux

# Setup Environment
ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml --tags setup_infra

cd ../connection

# Execute Integration tests for Linux
INVENTORY=../connection_aws_ssm/inventory-linux.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    -e action_prefix= \
    "$@" || true

# Execute Integration tests for Windows
INVENTORY=../connection_aws_ssm/inventory-windows.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    -e action_prefix= \
    "$@" || true

cd ../connection_aws_ssm

# Destroy Environment
ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml --tags delete_infra
