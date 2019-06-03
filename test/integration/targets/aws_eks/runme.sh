#!/usr/bin/env bash

set -eux

# Test graceful failure for older versions of botocore
source virtualenv.sh
pip install 'botocore<1.10.0' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/old_version.yml "$@"

# Run full test suite
source virtualenv.sh
pip install 'botocore>=1.10.1' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/full_test.yml "$@"
