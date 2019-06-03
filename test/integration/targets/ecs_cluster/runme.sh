#!/usr/bin/env bash

set -eux

# Test graceful failure for older versions of botocore
source virtualenv.sh
pip install 'botocore<=1.7.40' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/network_fail.yml "$@"

# Test graceful failure for assign public ip
# applies for botocore >= 1.7.44 and < 1.8.4
source virtualenv.sh
pip install 'botocore>=1.7.44,<1.8.4' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/network_assign_public_ip_fail.yml "$@"

# Test graceful failure for force new deployment #42518
# applies for botocore < 1.8.4
source virtualenv.sh
pip install 'botocore>=1.7.44,<1.8.4' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/network_force_new_deployment_fail.yml "$@"

# Test force new deployment #42518
# applies for botocore < 1.8.4
source virtualenv.sh
pip install 'botocore>1.8.4' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/network_force_new_deployment.yml "$@"

# Run full test suite
source virtualenv.sh
pip install 'botocore>=1.10.37' boto3 # version 1.10.37 for scheduling strategy
ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/full_test.yml "$@"
