#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

function gen_task_files() {
    for i in $(seq -f '%03g' 1 39); do
        echo -e "- name: Hello Message\n  debug:\n    msg: Task file ${i}" > "tasks/hello/tasks-file-${i}.yml"
    done
}

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


## Max Recursion Depth
# https://github.com/ansible/ansible/issues/23609
ANSIBLE_STRATEGY='linear' ansible-playbook test_role_recursion.yml -i ../../inventory "$@" --skip-tags never

## Nested tasks
# https://github.com/ansible/ansible/issues/34782
ANSIBLE_STRATEGY='linear' ansible-playbook test_nested_tasks.yml  -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook test_nested_tasks.yml  -i ../../inventory "$@" --skip-tags never

## Tons of top level include_tasks
# https://github.com/ansible/ansible/issues/36053
# Fixed by https://github.com/ansible/ansible/pull/36075
gen_task_files
ANSIBLE_STRATEGY='linear' ansible-playbook test_copious_include_tasks.yml  -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook test_copious_include_tasks.yml  -i ../../inventory "$@" --skip-tags never
rm -f tasks/hello/*.yml
