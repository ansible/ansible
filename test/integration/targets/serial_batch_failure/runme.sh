#!/usr/bin/env bash

set -eux

# Test default behavior - playbook should stop after first batch fails
ansible-playbook test_default_behavior.yml -i inventory -e "test_name=default_behavior" "$@" 2>&1 | tee /tmp/serial_test_default.out
grep -q "host3 should not execute" /tmp/serial_test_default.out && exit 1 || echo "✓ Default behavior: execution stopped as expected"

# Test continue on batch failure - playbook should continue to all hosts
ansible-playbook test_continue_enabled.yml -i inventory -e "test_name=continue_enabled" "$@" 2>&1 | tee /tmp/serial_test_continue.out
grep -q "host3 executed" /tmp/serial_test_continue.out || (echo "✗ Continue enabled: host3 should have executed" && exit 1)
echo "✓ Continue enabled: all hosts executed"

# Test with rescue blocks
ansible-playbook test_with_rescue.yml -i inventory "$@"
echo "✓ Rescue blocks work correctly"

# Test with max_fail_percentage - playbook should fail but we verify behavior
ansible-playbook test_max_fail_percentage.yml -i inventory "$@" 2>&1 | tee /tmp/serial_test_max_fail.out || true
# Verify the second play did NOT execute (should stop when max_fail_percentage reached)
grep -q "max_fail_percentage test completed" /tmp/serial_test_max_fail.out && exit 1 || echo "✓ max_fail_percentage interaction works"

echo "All integration tests passed!"
