#!/usr/bin/env bash
echo "Testing that ansible-test sanity actually ignores files when passed with the --fix flag"

TESTFILE="./no_trailing_newline.txt"
RESULTFILE="$OUTPUT_DIR/fix_filter_results.txt"

trap 'echo -n "no trailing newline" > $TESTFILE' EXIT

ansible-test sanity --test trailing-newline --fix &> "$RESULTFILE"

# No error
if grep -q "ERROR: test/sanity/ignore.txt.*Ignoring 'test/integration/targets/ansible-test-sanity/no_trailing_newline.txt' is unnecessary" "$RESULTFILE"; then
	exit 1
fi

# no_trailing_newline.txt is in ignore.txt and it should not have been fixed
if [[ $(tail -c1 "no_trailing_newline.txt" | wc -l) -eq 1 ]]; then
	exit 1
fi
