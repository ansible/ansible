#!/usr/bin/env bash

set -eux


SCRIPT_PATH=$(realpath "$ANSIBLE_TEST_ANSIBLE_LIB_ROOT/../../test/sanity/code-smell/trailing-newline.py")

TEST_DIR=$(mktemp -d)
RESULTS="$TEST_DIR/results.txt"
HAS_NEWLINE="$TEST_DIR/has_newline.py"
NO_NEWLINE="$TEST_DIR/no_newline.py"

trap 'rm -rf "$TEST_DIR"' EXIT

echo "# test" > "$HAS_NEWLINE"
echo -n "# test" > "$NO_NEWLINE"

export ANSIBLE_TEST_FIX_MODE=0

# Check that sanity fails NO_NEWLINE, and succeeds on HAS_NEWLINE
python "$SCRIPT_PATH" "$HAS_NEWLINE" "$NO_NEWLINE" | tee "$RESULTS"  
cat "$RESULTS"
! grep -q "$HAS_NEWLINE: text files should end with a newline character" "$RESULTS"
grep -q "$NO_NEWLINE: text files should end with a newline character" "$RESULTS"

# Fix file, check no errors
ANSIBLE_TEST_FIX_MODE=1 python "$SCRIPT_PATH" "$NO_NEWLINE" "$HAS_NEWLINE" | tee "$RESULTS"
cat "$RESULTS"
! grep -q "$NO_NEWLINE: text files should end with a newline character" "$RESULTS"
! grep -q "$HAS_NEWLINE: text files should end with a newline character" "$RESULTS"

# Check again for no errors after fix
python "$SCRIPT_PATH" "$HAS_NEWLINE" "$NO_NEWLINE" | tee "$RESULTS"  
cat "$RESULTS"
! grep -q "$NO_NEWLINE: text files should end with a newline character" "$RESULTS"
! grep -q "$HAS_NEWLINE: text files should end with a newline character" "$RESULTS"

# Manual check for sanity (count newlines in last byte of file)
[[ $(tail -c1 "$NO_NEWLINE" | wc -l) -gt 0 ]]
