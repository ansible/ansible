#!/usr/bin/env bash

set -eux

# https://github.com/ansible/ansible/pull/42528

export SELECTED_STRATEGY

for strategy in linear free; do
  SELECTED_STRATEGY="${strategy}"

  ansible-playbook non_integer_throttle.yml -i inventory "$@" 2>&1 | grep "Failed to convert the throttle value to an integer: invalid literal for int"
  ansible-playbook undefined_throttle.yml -i inventory "$@" 2>&1 | grep "Failed to convert the throttle value to an integer: 'nope' is undefined"

  ansible-playbook test_throttle.yml -i inventory --forks 12 "$@"
done
