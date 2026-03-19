#!/usr/bin/env bash

set -eux

# Test 1: max_fail_percentage with nested include_tasks inside blocks
# Reproduces https://github.com/ansible/ansible/issues/86574
#
# With max_fail_percentage: 0 and 2 hosts, any single failure should
# halt the play for all hosts. When the failure occurs inside a nested
# block via include_tasks, the fix ensures the failure is counted
# immediately (via failed_hosts) rather than waiting for the iterator
# to reach a terminal state (via _tqm._failed_hosts).

set +e
ansible-playbook test_nested.yml -i inventory "$@" > output.log 2>&1
result=$?
set -e

cat output.log

# Playbook should exit with non-zero (hosts failed)
if [ "$result" -eq 0 ]; then
    echo "FAIL: Playbook should have failed but succeeded"
    exit 1
fi

# The Marker task should NOT have run for any host, because
# max_fail_percentage: 0 should halt the play after the first failure.
if grep -q "marker task on" output.log; then
    echo "FAIL: Marker task ran but should have been stopped by max_fail_percentage"
    exit 1
fi

# The always section should have run for all hosts
if [ "$(grep -c '"msg": "always cleanup"' output.log)" -ne 2 ]; then
    echo "FAIL: Always tasks did not run for all hosts"
    exit 1
fi

echo "Tests passed!"
