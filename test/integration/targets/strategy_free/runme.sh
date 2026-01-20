#!/usr/bin/env bash

set -eux

export ANSIBLE_STRATEGY=free

set +e
result="$(ansible-playbook test_last_include_in_always.yml -i inventory "$@" 2>&1)"
set -e
grep -q "INCLUDED TASK EXECUTED" <<< "$result"

set +e
result="$(ansible-playbook test_run_once.yml -i testhost,testhost2 "$@" 2>&1)"
set -e
no_run_once="\[WARNING\]: Using run_once with the free strategy is not currently supported\."
grep -q "$no_run_once" <<< "$result"
[ "$(grep -c 'EXPECTED' <<< "$result")" -eq 1 ]
