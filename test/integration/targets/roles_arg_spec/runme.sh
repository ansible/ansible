#!/usr/bin/env bash

set -eux

# This effectively disables junit callback output by directing the output to
# a directory ansible-test will not look at.
#
# Since the failures in these tests are on the role arg spec validation and the
# name for those tasks is fixed (we cannot add "EXPECTED FAILURE" to the name),
# disabling the junit callback output is the easiest way to prevent these from
# showing up in test run output.
#
# Longer term, an option can be added to the junit callback allowing a custom
# regexp to be supplied rather than the hard coded "EXPECTED FAILURE".
export JUNIT_OUTPUT_DIR="${OUTPUT_DIR}"

# Various simple role scenarios
ansible-playbook test.yml -i ../../inventory "$@"

# More complex role test
ansible-playbook test_complex_role_fails.yml -i ../../inventory "$@"

# Test play level role will fail
set +e
ansible-playbook test_play_level_role_fails.yml -i ../../inventory "$@"
test $? -ne 0
set -e

# Test the validation task is tagged with 'always' by specifying an unused tag.
# The task is tagged with 'foo' but we use 'bar' in the call below and expect
# the validation task to run anyway since it is tagged 'always'.
ansible-playbook test_tags.yml -i ../../inventory "$@" --tags bar | grep "a : Validating arguments against arg spec 'main' - Main entry point for role A."

# Test validation with various values for "tasks_from"
ansible-playbook test_path_extension.yml -i ../../inventory "$@" 2>&1 | tee out.txt
count="$(grep -c 'TASK.*Validating arguments against arg spec' out.txt)"
expected_count="$(grep -c import_role test_path_extension.yml)"
if [ "$count" -ne "$expected_count" ]; then
    echo "Failed to find the expected number of argument spec validation tasks"
    exit 1
fi
