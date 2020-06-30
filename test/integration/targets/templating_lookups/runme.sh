#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=./ UNICODE_VAR=café ansible-playbook runme.yml "$@"

ansible-playbook template_lookup_vaulted/playbook.yml --vault-password-file template_lookup_vaulted/test_vault_pass "$@"

ansible-playbook template_deepcopy/playbook.yml -i template_deepcopy/hosts "$@"

# https://github.com/ansible/ansible/issues/66943
ansible-playbook template_lookup_safe_eval_unicode/playbook.yml "$@"
