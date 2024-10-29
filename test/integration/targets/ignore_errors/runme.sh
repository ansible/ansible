#!/usr/bin/env bash
set -eux

ansible-playbook -i ../../inventory test_ignore_errors.yml "$@"

if ansible-playbook -i ../../inventory test_ignore_errors_false.yml "$@" > out.txt; then
    echo 'Playbook expected to fail succeeded'
    exit 1
fi
# The first task should fail and not be ignored
grep out.txt -e 'ok=0' | grep 'ignored=0' | grep 'failed=1'
