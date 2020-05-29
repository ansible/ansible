#!/usr/bin/env bash

set -eux

ansible-playbook unicode.yml -i inventory -v -e 'extra_var=café' "$@"
# Test the start-at-task flag #9571
ANSIBLE_HOST_PATTERN_MISMATCH=warning ansible-playbook unicode.yml -i inventory -v --start-at-task '*¶' -e 'start_at_task=True' "$@"

# Test --version works with non-ascii ansible project paths #66617
# Unset these so values from the project dir are used
unset ANSIBLE_CONFIG
unset ANSIBLE_LIBRARY
pushd křížek-ansible-project && ansible --version; popd
