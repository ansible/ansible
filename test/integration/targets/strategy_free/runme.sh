#!/usr/bin/env bash

set -eux

export ANSIBLE_STRATEGY=free

set +e
result="$(ansible-playbook test_last_include_in_always.yml -i inventory "$@" 2>&1)"
set -e
grep -q "INCLUDED TASK EXECUTED" <<< "$result"

set +e
result="$(ansible-playbook free_index_error.yml -i free_hosts "$@" 2>&1)"
set -e
grep -q "\[host1\]: UNREACHABLE!" <<< "$result"
if grep -q "IndexError: list index out of range" <<< "$result"; then
    exit 1
fi

result="$(ansible-playbook test_run_once_noop.yml -i free_hosts "$@" 2>&1)"
grep "Using run_once with the free strategy is not currently supported." <<< "$result"
