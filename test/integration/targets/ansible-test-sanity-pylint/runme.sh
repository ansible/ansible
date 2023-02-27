#!/usr/bin/env bash

set -eu

source ../collection/setup.sh

# Create test scenarios at runtime that do not pass sanity tests.
# This avoids the need to create ignore entries for the tests.

echo "
from ansible.utils.display import Display

display = Display()
display.deprecated('', version='2.0.0', collection_name='ns.col')" >> plugins/lookup/deprecated.py

# Verify deprecation checking works for normal releases and pre-releases.

for version in 2.0.0 2.0.0-dev0; do
  echo "Checking version: ${version}"
  sed "s/^version:.*\$/version: ${version}/" < galaxy.yml > galaxy.yml.tmp
  mv galaxy.yml.tmp galaxy.yml
  ansible-test sanity --test pylint --color --failure-ok --lint "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
  diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
  grep -f "${TEST_DIR}/expected.txt" actual-stderr.txt
done
