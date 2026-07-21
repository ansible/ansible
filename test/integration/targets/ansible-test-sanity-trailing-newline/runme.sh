#!/usr/bin/env bash


set -e
SCRIPT_PATH="$ANSIBLE_TEST_ANSIBLE_LIB_ROOT/../../test/sanity/code-smell/trailing-newline.py"

RESULTS="$OUTPUT_DIR/trailing_newline_results.txt"
HAS_NEWLINE="$OUTPUT_DIR/has_newline.py"
NO_NEWLINE="$OUTPUT_DIR/no_newline.py"

echo "# test" > "$HAS_NEWLINE"
echo -n "# test" > "$NO_NEWLINE"

export ANSIBLE_TEST_FIX_MODE=0

# Check that sanity fails NO_NEWLINE, and succeeds on HAS_NEWLINE
python "$SCRIPT_PATH" "$HAS_NEWLINE" "$NO_NEWLINE" | tee "$RESULTS"
if grep -q "$HAS_NEWLINE: text files should end with a newline character" "$RESULTS"; then
    exit 1
fi
grep -q "$NO_NEWLINE: text files should end with a newline character" "$RESULTS"

# Fix file, check no errors
ANSIBLE_TEST_FIX_MODE=1 python "$SCRIPT_PATH" "$NO_NEWLINE" "$HAS_NEWLINE" | tee "$RESULTS"
if grep -q "$NO_NEWLINE: text files should end with a newline character" "$RESULTS"; then
    exit 1
fi
if grep -q "$HAS_NEWLINE: text files should end with a newline character" "$RESULTS"; then
    exit 1
fi

# Check again for no errors after fix
python "$SCRIPT_PATH" "$HAS_NEWLINE" "$NO_NEWLINE" | tee "$RESULTS"
if grep -q "$NO_NEWLINE: text files should end with a newline character" "$RESULTS"; then
    exit 1
fi
if grep -q "$HAS_NEWLINE: text files should end with a newline character" "$RESULTS"; then
    exit 1
fi

# Manual check for sanity (count newlines in last byte of file)
[[ $(tail -c1 "$NO_NEWLINE" | wc -l) -gt 0 ]]
