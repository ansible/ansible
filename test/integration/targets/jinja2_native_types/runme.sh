#!/usr/bin/env bash

set -eux

export ANSIBLE_JINJA2_NATIVE=1
ansible-playbook runtests.yml -v "$@"
ansible-playbook --vault-password-file test_vault_pass test_vault.yml -v "$@"
ansible-playbook test_hostvars.yml -v "$@"
ansible-playbook nested_undefined.yml -v "$@"
unset ANSIBLE_JINJA2_NATIVE
