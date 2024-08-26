#!/usr/bin/env bash

COLLECTION_NAME=version source ../collection/setup.sh

set -eux

cd ../version
ansible-test sanity --test runtime-metadata --color --truncate 0 --failure-ok --lint "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected-version.txt" actual-stdout.txt
grep -F -f "${TEST_DIR}/expected-version.txt" actual-stderr.txt

cd ../no_version
ansible-test sanity --test runtime-metadata --color --truncate 0 --failure-ok --lint "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected-no_version.txt" actual-stdout.txt
grep -F -f "${TEST_DIR}/expected-no_version.txt" actual-stderr.txt
