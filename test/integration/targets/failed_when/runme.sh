#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook runme.yml "$@"

test "$(ansible-playbook 84558.yml "$@" 2>&1 | grep -c 'SHOULD_NOT_RUN')" = "0"
