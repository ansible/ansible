#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../../targets/

# Test graceful failure for older versions of botocore
source virtualenv.sh
pip install 'botocore<1.10.16' 'boto3<1.7.16'
ansible-playbook -v playbooks/version_fail.yml "$@"

# Run full test suite
source virtualenv.sh
pip install 'botocore>=1.10.16' boto3
ansible-playbook -v playbooks/full_test.yml "$@"
