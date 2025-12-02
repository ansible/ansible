#!/usr/bin/env bash

set -eux

ansible-playbook test_var_blending.yml -i inventory -e @test_vars.yml -v "$@"

# check bad vault file erros
[ "$(ansible-playbook error_handling.yml -i inventory --vault-password-file supersecretvaultsecret -e @vars/bad_vault.yml 2>&1 | grep -c 'dummy')" -eq "0" ]
[ "$(ansible-playbook error_handling.yml -i inventory --vault-password-file supersecretvaultsecret --tags includevault 2>&1 | grep -c 'dummy')" -eq "0" ]

# setup group file for bad vault tests
trap 'rm group_vars/local/bad_vault.yml' EXIT
ln -s "${PWD}/vars/bad_vault.yml" group_vars/local/
[ "$(ansible-playbook error_handling.yml -i inventory --vault-password-file supersecretvaultsecret 2>&1 | grep -c 'dummy')" -eq "0" ]
