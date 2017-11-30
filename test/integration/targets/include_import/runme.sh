#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

# Role
ansible-playbook role/test_include_role.yml -i ../../inventory "$@"
ansible-playbook role/test_import_role.yml -i ../../inventory "$@"

# Tasks
ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@"
ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@"

# Play
ansible-playbook play/test_import_play.yml -i ../../inventory "$@"
