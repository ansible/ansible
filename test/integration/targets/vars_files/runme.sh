#!/usr/bin/env bash

set -eux

ansible-playbook runme.yml -i inventory -v "$@"

output=$(ansible-playbook missing_vars_files.yml -i inventory -v "$@" 2>&1)
grep -F "Unable to find vars_files: doesnt_exist.yml, also_doesnt_exist.yml" <<< "$output"
grep -E "ok=2.*ignored=1" <<< "$output"
