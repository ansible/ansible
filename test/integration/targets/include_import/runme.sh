#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

function gen_task_files() {
    total_memory=$(get_memory)
    if [[ $total_memory -gt 8388608 ]]; then         # 8GiB
        upper_limit=300
    elif [[ $total_memory -gt 4194304 ]]; then       # 4GiB
        upper_limit=150
    elif [[ $total_memory -gt 2097152 ]]; then       # 2GiB
        upper_limit=75
    else
        upper_limit=16
    fi
    cleanup
    set +x
    for i in $(seq -f '%03g' 1 $upper_limit); do
        echo -e "- name: Hello Message\n  debug:\n    msg: Tasks file ${i}" > "tasks/hello/tasks-file-${i}.yml"
        echo -e "    - include_tasks: \"{{ playbook_dir }}/tasks/hello/tasks-file-${i}.yml\"" >> test_copious_include_tasks.yml
        echo -e "- name: Import ${i}\n  import_role:\n    name: role1\n    tasks_from: tasks_dynamic.yml\n" >> tasks/tasks_multiple_import_role_dynamic_tasks.yml
        echo -e "- name: Import ${i}\n  import_role:\n    name: role1\n    tasks_from: tasks_static.yml\n" >> tasks/tasks_multiple_import_role_static_tasks.yml
        echo -e "- name: Include ${i}\n  include_role:\n    name: role1\n    tasks_from: \"tasks_{{ tasks_file_name }}.yml\"\n" >> tasks/tasks_multiple_include_role.yml
    done
    set -x
}

function cleanup() {
    rm -f tasks/hello/*.yml
    rm -f tasks/tasks_multiple*
    sed -i '/include_tasks/d' test_copious_include_tasks.yml
}

function get_memory() {
    if [[ -f $(which sw_vers) ]]; then
        # macOS
        memory=$(sysctl hw.memsize | awk '{print $2}')
        memory=$((memory / 1024))
    else
        # Linux
        memory=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
    fi

    echo $memory
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

# https://github.com/ansible/ansible/issues/38357
gen_task_files
ANSIBLE_STRATEGY='linear' ansible-playbook test_inception.yml -i ../../inventory -e tasks_file_name=static "$@" --skip-tags never
ANSIBLE_STRATEGY='linear' ansible-playbook test_inception.yml -i ../../inventory -e tasks_file_name=dynamic "$@" --skip-tags never

## Nested tasks
# https://github.com/ansible/ansible/issues/34782
ANSIBLE_STRATEGY='linear' ansible-playbook test_nested_tasks.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook test_nested_tasks.yml -i ../../inventory "$@" --skip-tags never

## Tons of top level include_tasks
# https://github.com/ansible/ansible/issues/36053
# Fixed by https://github.com/ansible/ansible/pull/36075
ANSIBLE_STRATEGY='linear' ansible-playbook test_copious_include_tasks.yml -i ../../inventory "$@" --skip-tags never
ANSIBLE_STRATEGY='free' ansible-playbook test_copious_include_tasks.yml -i ../../inventory "$@" --skip-tags never
cleanup

# Inlcuded tasks should inherit attrs from non-dynamic blocks in parent chain
# https://github.com/ansible/ansible/pull/38827
ANSIBLE_STRATEGY='linear' ansible-playbook test_grandparent_inheritance.yml -i ../../inventory "$@"
