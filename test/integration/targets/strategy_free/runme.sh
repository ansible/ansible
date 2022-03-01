#!/usr/bin/env bash

set -eux

export ANSIBLE_STRATEGY=free

set +e
result="$(ansible-playbook test_last_include_in_always.yml -i inventory "$@" 2>&1)"
set -e
grep -q "INCLUDED TASK EXECUTED" <<< "$result"
