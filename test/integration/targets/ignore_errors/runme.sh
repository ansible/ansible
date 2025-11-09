#!/usr/bin/env bash
set -eux

# Run the original tests
ansible-playbook -i ../../inventory test_ignore_errors.yml "$@"

if ansible-playbook -i ../../inventory test_ignore_errors_false.yml "$@" > out.txt; then
    echo 'Playbook expected to fail succeeded'
    exit 1
fi
# The first task should fail and not be ignored
grep out.txt -e 'ok=0' | grep 'ignored=0' | grep 'failed=1'

# Test the new check_mode templating functionality to ensure the fix works
# Test in normal mode (ansible_check_mode should be false, so errors should NOT be ignored when ignore_errors="{{ ansible_check_mode }}")
ansible-playbook -i ../../inventory test_comprehensive_templating.yml "$@"

# Test in check mode to verify behavior there as well
ansible-playbook -i ../../inventory --check test_comprehensive_templating.yml "$@"
