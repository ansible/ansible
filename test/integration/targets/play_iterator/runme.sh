#!/usr/bin/env bash

set -eux

ansible-playbook playbook.yml --start-at-task 'task 2' "$@"

ansible-playbook playbook.yml --start-at-task 'task 2' \
    --extra-vars 'setup="{{ True }}" spec="test"' "$@" | tee out.txt

grep "TASK \[Gathering Facts\]" out.txt
grep "TASK \[Validating arguments against arg spec test\]" out.txt
grep "TASK \[task 2\]" out.txt
