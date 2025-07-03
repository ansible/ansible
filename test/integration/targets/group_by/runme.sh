#!/usr/bin/env bash

set -eux

ansible-playbook test_group_by.yml -i inventory.group_by -v "$@"
ANSIBLE_HOST_PATTERN_MISMATCH=warning ansible-playbook test_group_by_skipped.yml -i inventory.group_by -v "$@"
