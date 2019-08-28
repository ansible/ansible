#!/usr/bin/env bash

set -eux

# https://github.com/ansible/ansible/pull/42528
ANSIBLE_STRATEGY='linear' ansible-playbook test_throttle.yml -vv -i inventory --forks 12 "$@"
ANSIBLE_STRATEGY='free' ansible-playbook test_throttle.yml -vv -i inventory --forks 12 "$@"
