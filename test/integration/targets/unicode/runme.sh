#!/usr/bin/env bash

set -eux

ansible-playbook unicode.yml -i inventory -v -e 'extra_var=café' "$@"
# Test the start-at-task flag #9571
ANSIBLE_HOST_PATTERN_MISMATCH=warning ansible-playbook unicode.yml -i inventory -v --start-at-task '*¶' -e 'start_at_task=True' "$@"
