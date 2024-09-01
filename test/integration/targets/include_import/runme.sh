#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

function gen_task_files() {
    for i in $(printf "%03d " {1..39}); do
        echo -e "- name: Hello Message\n  debug:\n    msg: Task file ${i}" > "tasks/hello/tasks-file-${i}.yml"
    done
}

## Adhoc

ansible -m include_role -a name=role1 localhost

## Import (static)

# Playbook
ansible-playbook playbook/test_import_playbook.yml -i inventory "$@"

ANSIBLE_STRATEGY='linear' ansible-playbook playbook/test_import_playbook_tags.yml -i inventory "$@" --tags canary1,canary22,validate --skip-tags skipme

# Tasks
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_import_tasks.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_import_tasks_tags.yml -i inventory "$@" --tags tasks1,canary1,validate

# Role
ANSIBLE_STRATEGY='linear' ansible-playbook role/test_import_role.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook role/test_import_role.yml -i inventory "$@"


## Include (dynamic)

# Tasks
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_include_tasks.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_tasks_tags.yml -i inventory "$@" --tags tasks1,canary1,validate

# Role
ANSIBLE_STRATEGY='linear' ansible-playbook role/test_include_role.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook role/test_include_role.yml -i inventory "$@"

# https://github.com/ansible/ansible/issues/68515
ansible-playbook -v role/test_include_role_vars_from.yml 2>&1 | tee test_include_role_vars_from.out
test "$(grep -E -c 'Expected a string for vars_from but got' test_include_role_vars_from.out)" = 1

## Max Recursion Depth
# https://github.com/ansible/ansible/issues/23609
ANSIBLE_STRATEGY='linear' ansible-playbook test_role_recursion.yml -i inventory "$@"
ANSIBLE_STRATEGY='linear' ansible-playbook test_role_recursion_fqcn.yml -i inventory "$@"

## Nested tasks
# https://github.com/ansible/ansible/issues/34782
ANSIBLE_STRATEGY='linear' ansible-playbook test_nested_tasks.yml  -i inventory "$@"
ANSIBLE_STRATEGY='linear' ansible-playbook test_nested_tasks_fqcn.yml  -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_nested_tasks.yml  -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_nested_tasks_fqcn.yml  -i inventory "$@"

## Tons of top level include_tasks
# https://github.com/ansible/ansible/issues/36053
# Fixed by https://github.com/ansible/ansible/pull/36075
gen_task_files
ANSIBLE_STRATEGY='linear' ansible-playbook test_copious_include_tasks.yml  -i inventory "$@"
ANSIBLE_STRATEGY='linear' ansible-playbook test_copious_include_tasks_fqcn.yml  -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_copious_include_tasks.yml  -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_copious_include_tasks_fqcn.yml  -i inventory "$@"
rm -f tasks/hello/*.yml

# Included tasks should inherit attrs from non-dynamic blocks in parent chain
# https://github.com/ansible/ansible/pull/38827
ANSIBLE_STRATEGY='linear' ansible-playbook test_grandparent_inheritance.yml -i inventory "$@"
ANSIBLE_STRATEGY='linear' ansible-playbook test_grandparent_inheritance_fqcn.yml -i inventory "$@"

# undefined_var
ANSIBLE_STRATEGY='linear' ansible-playbook undefined_var/playbook.yml  -i inventory "$@"
ANSIBLE_STRATEGY='free' ansible-playbook undefined_var/playbook.yml  -i inventory "$@"

# include_ + apply (explicit inheritance)
ANSIBLE_STRATEGY='linear' ansible-playbook apply/include_apply.yml -i inventory "$@" --tags foo
set +e
OUT=$(ANSIBLE_STRATEGY='linear' ansible-playbook apply/import_apply.yml -i inventory "$@" --tags foo 2>&1 | grep 'ERROR! Invalid options for import_tasks: apply')
set -e
if [[ -z "$OUT" ]]; then
    echo "apply on import_tasks did not cause error"
    exit 1
fi

ANSIBLE_STRATEGY='linear' ANSIBLE_PLAYBOOK_VARS_ROOT=all ansible-playbook apply/include_apply_65710.yml -i inventory "$@"
ANSIBLE_STRATEGY='free' ANSIBLE_PLAYBOOK_VARS_ROOT=all ansible-playbook apply/include_apply_65710.yml -i inventory "$@"

# Test that duplicate items in loop are not deduped
ANSIBLE_STRATEGY='linear' ansible-playbook tasks/test_include_dupe_loop.yml -i inventory "$@" | tee test_include_dupe_loop.out
test "$(grep -c '"item=foo"' test_include_dupe_loop.out)" = 3
ANSIBLE_STRATEGY='free' ansible-playbook tasks/test_include_dupe_loop.yml -i inventory "$@" | tee test_include_dupe_loop.out
test "$(grep -c '"item=foo"' test_include_dupe_loop.out)" = 3

ansible-playbook public_exposure/playbook.yml -i inventory "$@"
ansible-playbook public_exposure/no_bleeding.yml -i inventory "$@"
ansible-playbook public_exposure/no_overwrite_roles.yml -i inventory "$@"

# https://github.com/ansible/ansible/pull/48068
ANSIBLE_HOST_PATTERN_MISMATCH=warning ansible-playbook run_once/playbook.yml "$@"

# https://github.com/ansible/ansible/issues/48936
ansible-playbook -v handler_addressing/playbook.yml 2>&1 | tee test_handler_addressing.out
test "$(grep -E -c 'include handler task|ERROR! The requested handler '"'"'do_import'"'"' was not found' test_handler_addressing.out)" = 2

# https://github.com/ansible/ansible/issues/49969
ansible-playbook -v parent_templating/playbook.yml 2>&1 | tee test_parent_templating.out
test "$(grep -E -c 'Templating the path of the parent include_tasks failed.' test_parent_templating.out)" = 0

# https://github.com/ansible/ansible/issues/54618
ansible-playbook test_loop_var_bleed.yaml "$@"

# https://github.com/ansible/ansible/issues/56580
ansible-playbook valid_include_keywords/playbook.yml "$@"

# https://github.com/ansible/ansible/issues/64902
ansible-playbook tasks/test_allow_single_role_dup.yml 2>&1 | tee test_allow_single_role_dup.out
test "$(grep -c 'ok=3' test_allow_single_role_dup.out)" = 1

# Test allow_duplicate with include_role and import_role
test "$(ansible-playbook tasks/test_dynamic_allow_dup.yml --tags include | grep -c 'Tasks file inside role')" = 2
test "$(ansible-playbook tasks/test_dynamic_allow_dup.yml --tags import | grep -c 'Tasks file inside role')" = 2

# test templating public, allow_duplicates, and rolespec_validate
ansible-playbook tasks/test_templating_IncludeRole_FA.yml 2>&1 | tee IncludeRole_FA_template.out
test "$(grep -c 'ok=6' IncludeRole_FA_template.out)" = 1
test "$(grep -c 'failed=0' IncludeRole_FA_template.out)" = 1

# https://github.com/ansible/ansible/issues/66764
ANSIBLE_HOST_PATTERN_MISMATCH=error ansible-playbook empty_group_warning/playbook.yml

ansible-playbook test_include_loop.yml "$@"
ansible-playbook test_include_loop_fqcn.yml "$@"

ansible-playbook include_role_omit/playbook.yml "$@"

# Test templating import_playbook, import_tasks, and import_role files
ansible-playbook playbook/test_templated_filenames.yml -e "pb=validate_templated_playbook.yml tasks=validate_templated_tasks.yml tasks_from=templated.yml" "$@" | tee out.txt
cat out.txt
test "$(grep out.txt -ce 'In imported playbook')" = 2
test "$(grep out.txt -ce 'In imported tasks')" = 3
test "$(grep out.txt -ce 'In imported role')" = 3

# https://github.com/ansible/ansible/issues/73657
ansible-playbook issue73657.yml 2>&1 | tee issue73657.out
test "$(grep -c 'SHOULD_NOT_EXECUTE' issue73657.out)" = 0

# https://github.com/ansible/ansible/issues/83874
ansible-playbook test_null_include_filename.yml 2>&1 | tee test_null_include_filename.out
test "$(grep -c 'ERROR! No file specified for ansible.builtin.include_tasks' test_null_include_filename.out)" = 1
test "$(grep -c 'The error appears to be in '\''.*/include_import/null_filename/tasks.yml'\'': line 4, column 3.*' test_null_include_filename.out)" = 1
test "$(grep -c '\- name: invalid include_task definition' test_null_include_filename.out)" = 1
