#!/usr/bin/env bash

set -eux

ansible-playbook runtests.yml -v "$@"
ansible-playbook --vault-password-file test_vault_pass test_vault.yml -v "$@"
ansible-playbook test_hostvars.yml -v "$@"
ansible-playbook nested_undefined.yml -v "$@"
ansible-playbook test_preserving_quotes.yml -v "$@"
