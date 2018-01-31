#!/usr/bin/env bash

set -eux

ansible-playbook test_includes.yml -i ../../inventory "$@"

PB_OUT=$(ansible-playbook test_include_task_in_include_role.yml -i ../../inventory "$@")
(echo "$PB_OUT" | grep -F "role (inner): yatta!") || exit 1
