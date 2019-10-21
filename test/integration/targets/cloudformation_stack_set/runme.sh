#!/usr/bin/env bash

set -eux

# Run full test suite
source virtualenv.sh
pip install 'botocore>1.10.26' boto3
ansible-playbook -i ../../inventory -v playbooks/full_test.yml "$@"
