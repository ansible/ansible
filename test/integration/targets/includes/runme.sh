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

# test 'rescuable' default (true) with each strategy
for strategy in linear free; do
    output="$(ansible-playbook include_role_error_handling.yml "$@" -e "strategy=${strategy}")"
    grep -q 'Rescue missing role include' <<< "$output"
    grep -q 'Continue after include_role error handling' <<< "$output"
    grep -q 'Verify host is available in later play' <<< "$output"
    grep -q 'failed=0' <<< "$output"
    grep -q 'rescued=1' <<< "$output"
done

# test 'rescuable' explicit true
ansible-playbook include_role_error_handling.yml "$@" -e '{"rescueme": true}'

# test missing tasks_from failure state
output="$(ansible-playbook include_role_error_handling.yml "$@" -e error_type=missing_tasks_from)"
grep -q 'Verify missing tasks_from failure details' <<< "$output"
grep -q 'Verify host is available in later play' <<< "$output"
grep -q 'failed=0' <<< "$output"
grep -q 'rescued=1' <<< "$output"

# test 'rescuable' explicit false
if ansible-playbook include_role_error_handling.yml "$@" -e '{"rescueme": false}'; then
    exit 1
fi

# test an include failure outside a rescuing block
set +e
output="$(ansible-playbook include_role_error_handling.yml "$@" -e error_type=unrescued 2>&1)"
rc=$?
set -e
test "$rc" -ne 0
grep -q 'localhost.*FAILED!' <<< "$output"
grep -q 'failed=1' <<< "$output"
grep -q 'rescued=0' <<< "$output"
if grep -q 'Continue after include_role error handling' <<< "$output" || grep -q 'Verify host is available in later play' <<< "$output"; then
    exit 1
fi
# ensure imports are not rescuable
[[ $(ansible-playbook import_no_rescue.yml "$@") != 0 ]]

# test for missing task_from when missing tasks/
ansible-playbook include_role_missing.yml "$@" 
