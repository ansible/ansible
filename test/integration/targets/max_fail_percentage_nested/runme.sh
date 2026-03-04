#!/usr/bin/env bash

set -eux

# The playbook should fail due to host1 failing in rescue block, 
# triggering max_fail_percentage: 24 (1/4 = 25%).
# Other hosts should NOT run the "Marker task".

set +e
ansible-playbook playbook.yml -i inventory "$@" > output.log 2>&1
result=$?
set -e

# Playbook should exit with non-zero
if [ $result -eq 0 ]; then
    echo "Playbook should have failed but succeeded"
    exit 1
fi

cat output.log

# Check that Marker task did NOT run for host2, host3, host4
if grep -q "Marker task" output.log; then
    echo "Marker task ran but should have been skipped by max_fail_percentage"
    exit 1
fi

# Check that we got the "NO MORE HOSTS LEFT" message
if ! grep -q "NO MORE HOSTS LEFT" output.log; then
    echo "NO MORE HOSTS LEFT message not found in output"
    exit 1
fi

echo "Test passed!"
