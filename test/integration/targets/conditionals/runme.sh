#!/usr/bin/env bash

set -eux

ANSIBLE_CONDITIONAL_BARE_VARS=1 ansible-playbook -i ../../inventory play.yml "$@"
ANSIBLE_CONDITIONAL_BARE_VARS=0 ansible-playbook -i ../../inventory play.yml "$@"

export ANSIBLE_CONDITIONAL_BARE_VARS=1
export ANSIBLE_DEPRECATION_WARNINGS=True

# No warnings for conditionals that are already type bool
test "$(ansible-playbook -i ../../inventory test_no_warnings.yml "$@" 2>&1 | grep -c '\[DEPRECATION WARNING\]')" = 0

# Warn for bare vars of other types since they may be interpreted differently when CONDITIONAL_BARE_VARS defaults to False
test "$(ansible-playbook -i ../../inventory test_warnings.yml "$@" 2>&1 | grep -c '\[DEPRECATION WARNING\]')" = 2
