#!/usr/bin/env bash

source ../collection/setup.sh

set -eux

ansible-test sanity --test validate-modules --color --truncate 0 --failure-ok --lint "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
grep -f "${TEST_DIR}/expected.txt" actual-stderr.txt

cd ../ps_only

if ! command -V pwsh; then
  echo "skipping test since pwsh is not available"
  exit 0
fi

# Use a PowerShell-only collection to verify that validate-modules does not load the collection loader multiple times.
ansible-test sanity --test validate-modules --color --truncate 0 "${@}"
