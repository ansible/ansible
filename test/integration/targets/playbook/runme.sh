#!/usr/bin/env bash

set -eux

# run type tests
ansible-playbook -i ../../inventory types.yml -v "$@"

# test timeout
ansible-playbook -i ../../inventory timeout.yml -v "$@"

# our Play class allows for 'user' or 'remote_user', but not both.
# first test that both user and remote_user work individually
set +e
result="$(ansible-playbook -i ../../inventory user.yml -v "$@" 2>&1)"
set -e
grep -q "worked with user" <<< "$result"
grep -q "worked with remote_user" <<< "$result"

# then test that the play errors if user and remote_user both exist
echo "EXPECTED ERROR: Ensure we fail properly if a play has both user and remote_user."
set +e
result="$(ansible-playbook -i ../../inventory remote_user_and_user.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! both 'user' and 'remote_user' are set for this play." <<< "$result"

# test that playbook errors if len(plays) == 0
echo "EXPECTED ERROR: Ensure we fail properly if a playbook is an empty list."
set +e
result="$(ansible-playbook -i ../../inventory empty.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! A playbook must contain at least one play" <<< "$result"

# test that play errors if len(hosts) == 0
echo "EXPECTED ERROR: Ensure we fail properly if a play has 0 hosts."
set +e
result="$(ansible-playbook -i ../../inventory empty_hosts.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! Hosts list cannot be empty. Please check your playbook" <<< "$result"

# test that play errors if tasks is malformed
echo "EXPECTED ERROR: Ensure we fail properly if tasks is malformed."
set +e
result="$(ansible-playbook -i ../../inventory malformed_tasks.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! A malformed block was encountered while loading tasks: 123 should be a list or None" <<< "$result"

# test that play errors if pre_tasks is malformed
echo "EXPECTED ERROR: Ensure we fail properly if pre_tasks is malformed."
set +e
result="$(ansible-playbook -i ../../inventory malformed_pre_tasks.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! A malformed block was encountered while loading pre_tasks" <<< "$result"

# test that play errors if post_tasks is malformed
echo "EXPECTED ERROR: Ensure we fail properly if post_tasks is malformed."
set +e
result="$(ansible-playbook -i ../../inventory malformed_post_tasks.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! A malformed block was encountered while loading post_tasks" <<< "$result"

# test roles: null -- it gets converted to [] internally
ansible-playbook -i ../../inventory roles_null.yml -v "$@"

# test roles: 123 -- errors
echo "EXPECTED ERROR: Ensure we fail properly if roles is malformed."
set +e
result="$(ansible-playbook -i ../../inventory malformed_roles.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! A malformed role declaration was encountered." <<< "$result"

# test roles: ["foo,bar"] -- errors about old style
echo "EXPECTED ERROR: Ensure we fail properly if old style role is given."
set +e
result="$(ansible-playbook -i ../../inventory old_style_role.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! Invalid old style role requirement: foo,bar" <<< "$result"

# test vars prompt that has no name
echo "EXPECTED ERROR: Ensure we fail properly if vars_prompt has no name."
set +e
result="$(ansible-playbook -i ../../inventory malformed_vars_prompt.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! Invalid vars_prompt data structure, missing 'name' key" <<< "$result"

# test vars_prompt: null
ansible-playbook -i ../../inventory vars_prompt_null.yml -v "$@"

# test vars_files: null
ansible-playbook -i ../../inventory vars_files_null.yml -v "$@"

# test vars_files: filename.yml
ansible-playbook -i ../../inventory vars_files_string.yml -v "$@"
