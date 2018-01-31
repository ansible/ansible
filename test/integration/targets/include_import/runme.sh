#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

## Import (static)

# Playbook
ANSIBLE_STRATEGY='linear' ansible-playbook playbook/test_import_playbook.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook playbook/test_import_playbook.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='linear' ansible-playbook playbook/test_import_playbook_tags.yml -i ../../inventory "$@" --tags canary1,canary22,validate --skip-tags skipme,never

# Tasks
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks_tags.yml -i ../../inventory "$@" --tags tasks1,canary1,validate --skip-tags never

# Role
ANSIBLE_STRATEGY='linear' ansible-playbook role/test_import_role.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook role/test_import_role.yml -i ../../inventory "$@" --skip-tags never


## Include (dynamic)

# Tasks
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks_tags.yml -i ../../inventory "$@" --tags tasks1,canary1,validate --skip-tags never

# Role
ANSIBLE_STRATEGY='linear' ansible-playbook role/test_include_role.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook role/test_include_role.yml -i ../../inventory "$@" --skip-tags never


## Recursion
# https://github.com/ansible/ansible/issues/23609
ANSIBLE_STRATEGY='linear' ansible-playbook test_recursion.yml -i ../../inventory "$@" --skip-tags never

## Nested tasks
# https://github.com/ansible/ansible/issues/34782
ANSIBLE_STRATEGY='linear' ansible-playbook nested.yml  -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook nested.yml  -i ../../inventory "$@" --skip-tags never
