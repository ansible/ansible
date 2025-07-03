#!/usr/bin/env bash

source ../collection/setup.sh

set -eux

ansible-test sanity --test validate-modules --color --truncate 0 --failure-ok --lint "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
grep -F -f "${TEST_DIR}/expected.txt" actual-stderr.txt

cd ../col
ansible-test sanity --test runtime-metadata

cd ../failure
if ansible-test sanity --test runtime-metadata 2>&1 | tee out.txt; then
  echo "runtime-metadata in failure should be invalid"
  exit 1
fi
grep out.txt -e 'extra keys not allowed'

cd ../ps_only

if ! command -V pwsh; then
  echo "skipping test since pwsh is not available"
  exit 0
fi

# Use a PowerShell-only collection to verify that validate-modules does not load the collection loader multiple times.
ansible-test sanity --test validate-modules --color --truncate 0 "${@}"

cd ../failure

if ansible-test sanity --test validate-modules --color --truncate 0 "${@}" 1> ansible-stdout.txt 2> ansible-stderr.txt; then
  echo "ansible-test sanity for failure should cause failure"
  exit 1
fi

cat ansible-stdout.txt
grep -q "ERROR: plugins/modules/failure_ps.ps1:0:0: import-error: Exception attempting to import module for argument_spec introspection" < ansible-stdout.txt
grep -q "test inner error message" < ansible-stdout.txt

cat ansible-stderr.txt
grep -q "FATAL: The 1 sanity test(s) listed below (out of 1) failed" < ansible-stderr.txt
grep -q "validate-modules" < ansible-stderr.txt
