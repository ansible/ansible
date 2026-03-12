#!/usr/bin/env bash

set -eux

# Test 1: Nested blocks with max_fail_percentage
# The playbook should NOT fail immediately due to max_fail_percentage 
# but should allow rescue/always tasks to run.
# However, it SHOULD stop before the Marker task.

set +e
ansible-playbook test_nested.yml -i inventory "$@" > output.log 2>&1
result=$?
set -e

# Playbook should exit with non-zero
if [ $result -eq 0 ]; then
    echo "Test 1: Playbook should have failed but succeeded"
    exit 1
fi

cat output.log

# Check that Marker task did NOT run for host2, host3, host4
if grep -q "Marker task" output.log; then
    echo "Test 1: Marker task ran but should have been skipped by max_fail_percentage"
    exit 1
fi

# Check that rescue and always tasks DID run for all hosts
# host1 fails in block, so it goes to rescue.
# max_fail_percentage: 24 (1/4 = 25% > 24%) should trigger.
# This should mark host2, host3, host4 as failed, but they should run rescue/always.
if [ $(grep -c '"msg": "rescue cleanup"' output.log) -ne 4 ]; then
    echo "Test 1: Rescue tasks did not run for all 4 hosts"
    exit 1
fi

if [ $(grep -c '"msg": "always cleanup"' output.log) -ne 4 ]; then
    echo "Test 1: Always tasks did not run for all 4 hosts"
    exit 1
fi

# Test 2: Serial batches and cumulative max_fail_percentage
# 10 hosts, serial: 2, max_fail_percentage: 25.
# Batch 1: 1 failure. Total failed = 1. Total hosts = 10. 1/10 = 10% <= 25%.
# So Batch 1 should NOT stop early.
# Batch 2: 1 failure. Total failed = 2. Total hosts = 10. 2/10 = 20% <= 25%.
# Batch 3: 1 failure. Total failed = 3. Total hosts = 10. 3/10 = 30% > 25%.
# So Batch 3 SHOULD trigger max_fail_percentage.

cat <<EOF > inventory_serial
host[1:10] ansible_connection=local
EOF

cat <<EOF > test_serial.yml
- hosts: all
  gather_facts: false
  serial: 2
  max_fail_percentage: 25
  tasks:
    - name: Fail on host1, host3, host5
      fail:
        msg: "failing host {{ inventory_hostname }}"
      when: inventory_hostname in ['host1', 'host3', 'host5']

    - name: This task should run for host1, host2, host3, host4 but NOT for the rest
      debug:
        msg: "Task running on {{ inventory_hostname }}"
EOF

set +e
ansible-playbook test_serial.yml -i inventory_serial "$@" > output_serial.log 2>&1
result=$?
set -e

cat output_serial.log

# host1 in Batch 1 fails. 1/10 = 10% <= 25%. Task 2 should run for host2 (which didn't fail).
if ! grep -q "Task running on host2" output_serial.log; then
    echo "Test 2: Task 2 should have run for host2"
    exit 1
fi

# host3 in Batch 2 fails. 2/10 = 20% <= 25%. Task 2 should run for host4.
if ! grep -q "Task running on host4" output_serial.log; then
    echo "Test 2: Task 2 should have run for host4"
    exit 1
fi

# host5 in Batch 3 fails. 3/10 = 30% > 25%. 
# This should fail the rest of the batch (host6) and stop future batches.
# Task 2 should NOT run for host5, host6, host7, host8, host9, host10.
for i in {5..10}; do
    if grep -q "Task running on host$i" output_serial.log; then
        echo "Test 2: Task 2 should NOT have run for host$i"
        exit 1
    fi
done

echo "Tests passed!"
