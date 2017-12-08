#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

## Import (static)

# Role
# ANSIBLE_STRATEGY='linear' ansible-playbook role/test_import_role.yml -i ../../inventory "$@"
# ANSIBLE_STRATEGY='free' ansible-playbook role/test_import_role.yml -i ../../inventory "$@"

# Tasks
# ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@"
# ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@"

# Playbook
# ANSIBLE_STRATEGY='linear' ansible-playbook playbook/test_import_playbook.yml -i ../../inventory "$@"
# ANSIBLE_STRATEGY='free' ansible-playbook playbook/test_import_playbook.yml -i ../../inventory "$@"


## Include (dynamic)

# Role
# ANSIBLE_STRATEGY='linear' ansible-playbook role/test_include_role.yml -i ../../inventory "$@"
# ANSIBLE_STRATEGY='free' ansible-playbook role/test_include_role.yml -i ../../inventory "$@"

# Tasks
# ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@"
# ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@"



## Recursion
# https://github.com/ansible/ansible/issues/23609
ANSIBLE_STRATEGY='linear' ansible-playbook test_recursion.yml -i ../../inventory "$@"
