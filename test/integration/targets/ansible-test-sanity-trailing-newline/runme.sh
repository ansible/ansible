#!/usr/bin/env bash

set -eu

# Navigate to project root
cd ../../../../../../../../..

TEST_DIR="lib/ansible/module_utils/newlinetests"
RESULTS="$TEST_DIR/results.txt"
HAS_NEWLINE="$TEST_DIR/has_newline.py"
NO_NEWLINE="$TEST_DIR/no_newline.py"

trap 'rm -rf "$TEST_DIR"' EXIT

mkdir -p "$TEST_DIR"
echo "# test" > "$HAS_NEWLINE"
echo -n "# test" > "$NO_NEWLINE"

set -x

echo "Check successful test"
ansible-test sanity --test trailing-newline "$HAS_NEWLINE" "${@}"

echo "Check that sanity test fail"
ansible-test sanity --test trailing-newline "$NO_NEWLINE" "${@}" > "$RESULTS" || true
cat "$RESULTS"
grep -q "ERROR: $NO_NEWLINE:0:0: text files should end with a newline character" "$RESULTS"

echo "Attempt to fix"
ansible-test sanity --test trailing-newline --fix "$NO_NEWLINE" "${@}" > "$RESULTS"
grep -v "ERROR: $NO_NEWLINE:0:0: text files should end with a newline character" "$RESULTS"

echo "Check for success after fix"
ansible-test sanity --test trailing-newline "$NO_NEWLINE" "${@}"
# Manual check for sanity (count newlines in last byte of file)
[[ $(tail -c1 "$NO_NEWLINE" | wc -l) -gt 0 ]]
