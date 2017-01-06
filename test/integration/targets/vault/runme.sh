#!/usr/bin/env bash

set -eux


ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password --list-tasks
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password --list-hosts
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password --syntax-check
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password
ansible-playbook test_vault_embedded.yml -i ../../inventory -v "$@" --vault-password-file vault-password --syntax-check
ansible-playbook test_vault_embedded.yml -i ../../inventory -v "$@" --vault-password-file vault-password
ansible-playbook test_vaulted_inventory.yml -i vaulted.inventory -v "$@" --vault-password-file vault-password

