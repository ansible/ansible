#!/usr/bin/env bash

set -eux

export ANSIBLE_GATHERING=explicit

ansible-playbook test_includes.yml -i ../../inventory "$@"

ansible-playbook inherit_notify.yml "$@"

echo "EXPECTED ERROR: Ensure we fail if using 'include' to include a playbook."
set +e
result="$(ansible-playbook -i ../../inventory include_on_playbook_should_fail.yml -v "$@" 2>&1)"
set -e
grep -q "'include_tasks' is not a valid attribute for a Play" <<< "$result"

ansible-playbook includes_loop_rescue.yml --extra-vars strategy=linear "$@"
ansible-playbook includes_loop_rescue.yml --extra-vars strategy=free "$@"

ansible-playbook includes_from_dedup.yml -i ../../inventory "$@"

# test 'rescueable' default (true)
ansible-playbook include_role_error_handling.yml "$@"
# test 'rescueable' explicit true 
ansible-playbook include_role_error_handling.yml "$@" -e '{"rescueme": true}'
# test 'rescueable' explicit false 
[[ $(ansible-playbook include_role_error_handling.yml "$@" -e '{"rescueme": false}') != 0 ]]
# ensure imports are not rescuable
[[ $(ansible-playbook import_no_rescue.yml "$@") != 0 ]]

# test for missing task_from when missing tasks/
ansible-playbook include_role_missing.yml "$@" 
