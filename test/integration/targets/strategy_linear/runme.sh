#!/usr/bin/env bash

set -eux

ansible-playbook test_include_file_noop.yml -i inventory "$@"

set +e
result="$(ansible-playbook test_55515.yml -i inventory "$@" 2>&1)"
set -e
grep -q "always" <<< "$result"
