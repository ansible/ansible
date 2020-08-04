#!/usr/bin/env bash

set -eux

ansible-playbook reserved_varname_warning.yml "$@" | grep -E 'Found variable using reserved name: namespace'
