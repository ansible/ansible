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
grep -q "IndexError: list index out of range" <<< "$result" && exit 1

# https://github.com/ansible/ansible/issues/87709
set +e
../test_utils/scripts/timeout.py 30 -- ansible-playbook broken_pipe.yml -i broken_pipe_hosts "$@" 2> "${OUTPUT_DIR}/broken_pipe_stderr.txt" | head -n 1
rc="${PIPESTATUS[0]}"
set -e
# 124 is timeout.py's timeout status, which is the pre-fix hang. This check is what separates fixed from unfixed.
[[ "$rc" -ne 0 && "$rc" -ne 124 ]]
grep -q "Broken pipe" "${OUTPUT_DIR}/broken_pipe_stderr.txt"
