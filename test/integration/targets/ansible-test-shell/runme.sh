#!/usr/bin/env bash
# Make sure that `ansible-test shell` outputs to the correct stream.

set -eu

source ../collection/setup.sh

set -x

# Try `shell` with delegation.

ansible-test shell --venv -- \
  python -c 'import sys; print("stdout"); print("stderr", file=sys.stderr)' 1> actual-stdout.txt 2> actual-stderr.txt

cat actual-stdout.txt
cat actual-stderr.txt

diff -u "${TEST_DIR}/expected-stdout.txt" actual-stdout.txt
grep -f "${TEST_DIR}/expected-stderr.txt" actual-stderr.txt

# Try `shell` without delegation.

ansible-test shell -- \
  python -c 'import sys; print("stdout"); print("stderr", file=sys.stderr)' 1> actual-stdout.txt 2> actual-stderr.txt

cat actual-stdout.txt
cat actual-stderr.txt

diff -u "${TEST_DIR}/expected-stdout.txt" actual-stdout.txt
grep -f "${TEST_DIR}/expected-stderr.txt" actual-stderr.txt
