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

# Test unsupported role spec fields emit a warning
expected_warning="Role 'invalid_specs' entrypoint 'main' contains errors in the argument spec. Use -vvv to see details."
ansible localhost -m include_role -a "name=invalid_specs" 2>&1 | grep -e "$expected_warning"
ansible localhost -m include_role -a "name=invalid_specs" -vvv | tee details
grep "Role 'invalid_specs' \(.*\) argument spec 'main' contains errors:" details
invalid_specs=(
    "password: no_log"
    "auth.password: no_log"
    "option_with_suboptions: apply_defaults"
    "option_name: aliases"
    "option_with_env_fallback: fallback"
)
for spec in "${invalid_specs[@]}"; do
    grep "$spec" details
done

# Test a valid spec doesn't cause a warning
ansible-playbook test_tags.yml -i ../../inventory "$@" --tags bar 2> error
if [ -s error ]; then
    grep -v "\[WARNING\]: Role 'a' entrypoint 'main'" error
fi
