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

# Test unknown and unsupported role spec fields emit a warning
invalid_specs=("no_log" "no_log_suboption" "aliases" "apply_defaults" "fallback" "unknown_field")
for spec in "${invalid_specs[@]}"; do
    echo "Testing invalid role argument spec: containing $spec"

    # test warning requires no verbosity
    ansible localhost -m include_role -a "name=invalid_specs tasks_from=$spec" 2> error
    grep "\[WARNING\]: Role 'invalid_specs' entrypoint '${spec}'" error

    # test details are included in stdout with at least -vvv
    ansible localhost -m include_role -a "name=invalid_specs tasks_from=$spec" -vvv "$@" > out
    grep "Role 'invalid_specs' (.*) argument spec '${spec}' contains errors:" out

    if [[ "$spec" = "no_log" ]]; then
        option_and_field='password: no_log'
    elif [[ "$spec" = "no_log_suboption" ]]; then
        option_and_field='auth.password: no_log'
    elif [[ "$spec" = "aliases" ]]; then
        option_and_field="option_name: $spec"
    elif [[ "$spec" = "apply_defaults" ]]; then
        option_and_field="option_with_suboptions: $spec"
    elif [[ "$spec" = "fallback" ]]; then
        option_and_field="option_with_env_fallback: $spec"
    elif [[ "$spec" = "unknown_field" ]]; then
        option_and_field="option_name: choice, unknown"
    fi
    grep -e "- ${option_and_field}\. Supported parameters include: choices, default, description, elements, options, required, type, version_added\." out
done

# Test a valid spec doesn't cause a warning
ansible-playbook test_tags.yml -i ../../inventory "$@" --tags bar 2> error
if [ -s error ]; then
    grep -v "\[WARNING\]: Role 'a' entrypoint 'main'" error
fi
