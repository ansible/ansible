#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook lookups.yml "$@"

ansible-playbook template_lookup_vaulted.yml --vault-password-file test_vault_pass "$@"
