#!/usr/bin/env bash

set -eux

# run type tests
ansible-playbook -i ../../inventory types.yml -v "$@"

# test timeout
ansible-playbook -i ../../inventory timeout.yml -v "$@"

echo "EXPECTED ERROR: Ensure we fail properly if a playbook is an empty list."
set +e
result="$(ansible-playbook -i ../../inventory empty.yml -v "$@" 2>&1)"
set -e
grep -q "ERROR! A playbook must contain at least one play" <<< "$result"
