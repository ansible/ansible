#!/usr/bin/env bash

set -eux

ansible-playbook test_includes.yml -i ../../inventory "$@"

ansible-playbook inherit_notify.yml "$@"

echo "EXPECTED ERROR: Ensure we fail if using 'include' to include a playbook."
set +e
result="$(ansible-playbook -i ../../inventory include_on_playbook_should_fail.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! 'include' is not a valid attribute for a Play" <<< "$result"

ansible-playbook includes_loop_rescue.yml --extra-vars strategy=linear "$@"
ansible-playbook includes_loop_rescue.yml --extra-vars strategy=free "$@"
