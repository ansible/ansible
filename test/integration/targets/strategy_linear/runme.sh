#!/usr/bin/env bash

set -eux

ansible-playbook test_include_file_noop.yml -i inventory "$@"

ansible-playbook task_action_templating.yml -i inventory "$@"

ansible-playbook task_templated_run_once.yml -i inventory "$@"

if ansible-playbook test_max_fail_percentage.yml -i inventory "$@" | tee /dev/stderr | grep -q "SHOULD_NOT_HAPPEN"; then
  exit 1
fi
