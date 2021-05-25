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
