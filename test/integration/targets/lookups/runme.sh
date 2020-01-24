#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib

# UNICODE_VAR is used in testing the env lookup plugin unicode functionality
ANSIBLE_ROLES_PATH=../ UNICODE_VAR=café ansible-playbook lookups.yml "$@"

ansible-playbook template_lookup_vaulted.yml --vault-password-file test_vault_pass "$@"

ansible-playbook -i template_deepcopy/hosts template_deepcopy/playbook.yml "$@"
