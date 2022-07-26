#!/usr/bin/env bash
# Make sure that `ansible-test sanity --lint` outputs the correct format to stdout, even when delegation is used.

set -eu

# Create test scenarios at runtime that do not pass sanity tests.
# This avoids the need to create ignore entries for the tests.

mkdir -p ansible_collections/ns/col/plugins/modules

(
  cd ansible_collections/ns/col/plugins/modules

  echo '#!invalid' > python-wrong-shebang.py # expected module shebang "b'#!/usr/bin/python'" but found: b'#!invalid'
)

source ../collection/setup.sh

set -x

###
### Run the sanity test with the `--lint` option.
###

# Use the `--venv` option to verify that delegation preserves the output streams.
ansible-test sanity --test shebang --color --failure-ok --lint --venv "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
grep -f "${TEST_DIR}/expected.txt" actual-stderr.txt

# Run without delegation to verify direct output uses the correct streams.
ansible-test sanity --test shebang --color --failure-ok --lint        "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
grep -f "${TEST_DIR}/expected.txt" actual-stderr.txt

###
### Run the sanity test without the `--lint` option.
###

# Use the `--venv` option to verify that delegation preserves the output streams.
ansible-test sanity --test shebang --color --failure-ok --venv "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
grep -f "${TEST_DIR}/expected.txt" actual-stdout.txt
[ ! -s actual-stderr.txt ]

# Run without delegation to verify direct output uses the correct streams.
ansible-test sanity --test shebang --color --failure-ok "${@}"        1> actual-stdout.txt 2> actual-stderr.txt
grep -f "${TEST_DIR}/expected.txt" actual-stdout.txt
[ ! -s actual-stderr.txt ]
