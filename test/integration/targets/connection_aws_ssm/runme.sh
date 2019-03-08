#!/usr/bin/env bash

ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml --tags setup_infra
set -eux

cd ../connection

INVENTORY=../connection_aws_ssm/inventory.aws_ssm ./test.sh \
    -e target_hosts=aws_ssm \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    -e action_prefix= \
    "$@"

if [ "$?" -eq "0" ]; then
  echo "Test case passed , tear down infra"
else
  echo "Test case failed tera down infra"
  cd ../
  ansible-playbook -c local aws_ssm_integration_test_setup_teardown.yml --tags delete_infra
fi

