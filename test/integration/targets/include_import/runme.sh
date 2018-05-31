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
ANSIBLE_STRATEGY='linear' ansible-playbook playbook/test_import_playbook.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook playbook/test_import_playbook.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='linear' ansible-playbook playbook/test_import_playbook_tags.yml -i ../../inventory "$@" --tags canary1,canary22,validate --skip-tags skipme

# Tasks
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks_tags.yml -i ../../inventory "$@" --tags tasks1,canary1,validate

# Role
ANSIBLE_STRATEGY='linear' ansible-playbook role/test_import_role.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook role/test_import_role.yml -i ../../inventory "$@"


## Include (dynamic)

# Tasks
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks_tags.yml -i ../../inventory "$@" --tags tasks1,canary1,validate

# Role
ANSIBLE_STRATEGY='linear' ansible-playbook role/test_include_role.yml -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook role/test_include_role.yml -i ../../inventory "$@"


## Max Recursion Depth
# https://github.com/ansible/ansible/issues/23609
ANSIBLE_STRATEGY='linear' ansible-playbook test_role_recursion.yml -i ../../inventory "$@"

## Nested tasks
# https://github.com/ansible/ansible/issues/34782
ANSIBLE_STRATEGY='linear' ansible-playbook test_nested_tasks.yml  -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_nested_tasks.yml  -i ../../inventory "$@"

## Tons of top level include_tasks
# https://github.com/ansible/ansible/issues/36053
# Fixed by https://github.com/ansible/ansible/pull/36075
gen_task_files
ANSIBLE_STRATEGY='linear' ansible-playbook test_copious_include_tasks.yml  -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_copious_include_tasks.yml  -i ../../inventory "$@"
rm -f tasks/hello/*.yml

# Inlcuded tasks should inherit attrs from non-dynamic blocks in parent chain
# https://github.com/ansible/ansible/pull/38827
ANSIBLE_STRATEGY='linear' ansible-playbook test_grandparent_inheritance.yml -i ../../inventory "$@"

# undefined_var
ANSIBLE_STRATEGY='linear' ansible-playbook undefined_var/playbook.yml  -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook undefined_var/playbook.yml  -i ../../inventory "$@"

# Include path inheritance using host var for include file path
ANSIBLE_STRATEGY='linear' ansible-playbook include_path_inheritance/playbook.yml  -i ../../inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook include_path_inheritance/playbook.yml  -i ../../inventory "$@"

# include_ + apply (explicit inheritance)
ANSIBLE_STRATEGY='linear' ansible-playbook apply/include_apply.yml -i ../../inventory "$@" --tags foo
set +e
OUT=$(ANSIBLE_STRATEGY='linear' ansible-playbook apply/import_apply.yml -i ../../inventory "$@" --tags foo 2>&1 | grep 'ERROR! Invalid options for import_tasks: apply')
set -e
if [[ -z "$OUT" ]]; then
    echo "apply on import_tasks did not cause error"
    exit 1
fi
