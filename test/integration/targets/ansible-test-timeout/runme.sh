#!/usr/bin/env bash
# Test ansible-test timeout functionality and the timeout callback.

source ../collection/setup.sh

set -eux -o pipefail

# Prime the venv so timeouts don't risk leaving a broken venv.
ansible-test integration noop --venv --color --truncate 0

echo "=== Test 1: ansible-test timeout already expired ==="
ansible-test env --timeout 0.0001 2>&1 | tee test1-env.txt

if ansible-test integration sleep --venv --color --truncate 0 2>&1 | tee test1.txt; then
    echo "FAIL: expected ansible-test to fail due to expired timeout, but it passed."
    exit 1
fi

grep -q "test timeout expired" test1.txt
grep -q "timeout may be too short" test1-env.txt

echo "=== Test 2: ansible-test timeout fires during a test ==="
# Use the sleep target (a shell script) so ansible-playbook doesn't run
# and the timeout callback doesn't intercept.
ansible-test env --timeout 0.1

if ansible-test integration sleep --venv --color --truncate 0 2>&1 | tee test2.txt; then
    echo "FAIL: expected ansible-test to fail due to timeout, but it passed."
    exit 1
fi

grep -q "time limit" test2.txt

echo "=== Test 3: timeout callback with deadline already passed ==="
# The timeout margin equals the timeout duration, so the callback
# deadline is guaranteed to be in the past by the time it loads.
# ansible-test's own timeout check passes since the deadline itself hasn't
# expired yet at startup.
ansible-test env --timeout 0.167 2>&1 | tee test3-env.txt

if ansible-test integration pause --venv --color --truncate 0 2>&1 | tee test3.txt; then
    echo "FAIL: expected ansible-test to fail due to timeout traceback, but it passed."
    exit 1
fi

grep -q "Tests aborted by the timeout callback" test3.txt
grep -q "deadline exceeded by" test3.txt
grep -q "timeout may be too short" test3-env.txt && exit 1

echo "=== Test 4: timeout callback fires while process is hung ==="
# Use a longer timeout so the callback deadline is in the future when it
# loads. The pause target keeps ansible-playbook alive long enough for the
# timeout callback to fire.
ansible-test env --timeout 0.25

if ansible-test integration pause --venv --color --truncate 0 2>&1 | tee test4.txt; then
    echo "FAIL: expected ansible-test to fail due to timeout traceback, but it passed."
    exit 1
fi

grep -q "Tests aborted by the timeout callback" test4.txt
grep -q "remaining" test4.txt

echo PASS
