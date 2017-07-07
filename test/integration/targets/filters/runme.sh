#!/usr/bin/env bash

set -eux

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install jmespath

ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml -i ../../inventory -e @../../integration_config.yml "$@"
