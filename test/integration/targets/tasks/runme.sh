#!/usr/bin/env bash

set -eux

ansible-playbook playbook.yml

export ANSIBLE_ACTION_PLUGINS=action_plugins ANSIBLE_DEPRECATION_WARNINGS=True

ansible localhost -m test_rc "$@" && exit 1 || echo 'Task failed as expected'
ansible localhost -m test_rc "$@" 2>&1 | grep "\[DEPRECATION WARNING\]: Inferring a task failure from a non-zero \`rc\` is deprecated"
