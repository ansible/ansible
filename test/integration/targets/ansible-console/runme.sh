#!/usr/bin/env bash

set -eux

# This is a work-around for a bug in host pattern checking.
# Once the bug is fixed this can be removed.
# See: https://github.com/ansible/ansible/issues/83557#issuecomment-2231986971
unset ANSIBLE_HOST_PATTERN_MISMATCH

echo debug var=inventory_hostname | ansible-console '{{"localhost"}}'

echo include_role name=end_play | ansible-console localhost 2>&1 | tee err.txt
if grep -q "ERROR" err.txt; then
  echo "Failed to execute end_play"
  exit 1
fi
