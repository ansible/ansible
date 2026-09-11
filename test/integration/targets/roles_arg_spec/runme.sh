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

VALIDATION_TASK="Validating arguments against arg spec 'main' - Main entry point for role A."
MIXED_VALIDATION="Validating arguments against arg spec 'main' - Main entry point for mixed_tags role."
EMPTY_VALIDATION="Validating arguments against arg spec 'main' - Main entry point for role role_with_no_tasks."

# Tagged import_role: validation runs only for roles that still have work to do.

# When running with --tags foo, only the foo-tagged role should validate.
output=$(ansible-playbook test_tags.yml -i ../../inventory "$@" --tags foo)
test "$(echo "$output" | grep -c "$VALIDATION_TASK")" = 1

# When running with a tag that matches no role, nothing validates.
output=$(ansible-playbook test_tags.yml -i ../../inventory "$@" --tags bar)
test "$(echo "$output" | grep -c "$VALIDATION_TASK")" = 0

# When running with --skip-tags on a role's tag, that role's validation is skipped.
output=$(ansible-playbook test_tags.yml -i ../../inventory "$@" --skip-tags foo)
test "$(echo "$output" | grep -c "$VALIDATION_TASK")" = 2

# Without any tag filter, all roles validate.
output=$(ansible-playbook test_tags.yml -i ../../inventory "$@")
test "$(echo "$output" | grep -c "$VALIDATION_TASK")" = 3

# Mixed role/task tags (mkrizek): role tagged foo, task tagged bar.
# --tags bar still executes a role task, so validation must run for both invocations.
output=$(ansible-playbook test_tags_mixed.yml -i ../../inventory "$@" --tags bar)
test "$(echo "$output" | grep -c "$MIXED_VALIDATION")" = 2
echo "$output" | grep -q "bar-tagged task in mixed_tags"

# --skip-tags bar leaves the untagged role task runnable, so validation must still run.
output=$(ansible-playbook test_tags_mixed.yml -i ../../inventory "$@" --skip-tags bar)
test "$(echo "$output" | grep -c "$MIXED_VALIDATION")" = 2
echo "$output" | grep -q "untagged task in mixed_tags"
test "$(echo "$output" | grep -c "bar-tagged task in mixed_tags")" = 0

# Fully skipped role (no matching tags) should not validate.
output=$(ansible-playbook test_tags_mixed.yml -i ../../inventory "$@" --tags unrelated)
test "$(echo "$output" | grep -c "$MIXED_VALIDATION")" = 0

# Empty (argspec-only) role: matching tags validate; non-matching do not.
output=$(ansible-playbook test_tags_empty_role.yml -i ../../inventory "$@" --tags empty_role)
test "$(echo "$output" | grep -c "$EMPTY_VALIDATION")" = 1

output=$(ansible-playbook test_tags_empty_role.yml -i ../../inventory "$@" --tags nomatch)
test "$(echo "$output" | grep -c "$EMPTY_VALIDATION")" = 0
