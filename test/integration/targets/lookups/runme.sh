#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook lookups.yml "$@"

ansible-playbook template_lookup_vaulted.yml --vault-password-file test_vault_pass "$@"

ansible-playbook -i template_deepcopy/hosts template_deepcopy/playbook.yml "$@"

# https://github.com/ansible/ansible/issues/66943
ansible-playbook template_lookup_safe_eval_unicode/playbook.yml "$@"
