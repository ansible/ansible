#!/usr/bin/env bash

set -eu

source ../collection/setup.sh

# Verify deprecation checking works for normal releases and pre-releases.

for version in 2.0.0 2.0.0-dev0; do
  echo "Checking version: ${version}"
  sed "s/^version:.*\$/version: ${version}/" < galaxy.yml > galaxy.yml.tmp
  mv galaxy.yml.tmp galaxy.yml
  ansible-test sanity --test pylint --color --failure-ok --lint "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
  diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
  grep -f "${TEST_DIR}/expected.txt" actual-stderr.txt
done

echo "PASS"
