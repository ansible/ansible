#!/usr/bin/env bash
set -eux

# Execute Integration tests for Linux
ansible-playbook -c local -i localhost aws_ssm_integration_test_setup_teardown.yml --tags "setup_infra,linux"

cd ../connection

INVENTORY=../connection_aws_ssm/inventory.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    -e action_prefix= \
    "$@" || true

cd ../connection_aws_ssm

ansible-playbook -c local -i localhost aws_ssm_integration_test_setup_teardown.yml --tags "delete_infra"

# Execute Integration tests for Windows
ansible-playbook -c local -i localhost aws_ssm_integration_test_setup_teardown.yml --tags "setup_infra,windows"

cd ../connection

INVENTORY=../connection_aws_ssm/inventory.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    -e action_prefix= \
    "$@" || true

cd ../connection_aws_ssm
ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml --tags delete_infra
