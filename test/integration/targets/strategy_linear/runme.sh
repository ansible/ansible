#!/usr/bin/env bash

set -eux

ansible-playbook test_include_file_noop.yml -i inventory "$@"

ansible-playbook task_action_templating.yml -i inventory "$@"
