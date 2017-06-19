#!/usr/bin/env bash

set -eux

ansible-playbook test_group_by.yml -i inventory.group_by -v "$@"
