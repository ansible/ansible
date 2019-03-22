#!/usr/bin/env bash

set -eux

ansible-playbook test_var_precedence.yml -i inventory -v "$@" \
    -e 'extra_var=extra_var' \
    -e 'extra_var_override=extra_var_override'

./ansible-var-precedence-check.py
