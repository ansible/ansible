#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -ex

ansible-playbook -i ../../inventory -e @../../integration_config.yml -v playbooks/full_test.yml "$@"
