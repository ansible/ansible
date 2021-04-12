#!/usr/bin/env bash

set -eux

export ANSIBLE_SHOW_CUSTOM_STATS=yes

# Simple tests
ansible-playbook test_simple.yml

# This playbook does two set_stats calls setting my_int to 10 and 15.
# The aggregated output should add to 25.
output=$(ansible-playbook test_aggregate.yml | grep '"my_int": 25' | wc -l)
test "$output" -eq 1
