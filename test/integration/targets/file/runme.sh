#!/usr/bin/env bash

set -ux

# run role type from runme.sh
export ANSIBLE_BECOME_ALLOW_SAME_USER=1
export ANSIBLE_ROLES_PATH=../
ansible-playbook -i ../../inventory runme.yml -v "$@"

# output tests on error
[ $(ansible -m debug -a 'msg={{ q("file", "/idontexist") }}' localhost) != 0 ]
ansible -m debug -a 'msg={{ q("file", "/idontexist", errors="warn") }}' localhost 2>&1 | grep '[WARNING]: Lookup failed but the error is being ignored'
ansible -m debug -a 'msg={{ q("file", "/idontexist", errors="ignore") }}' localhost 2>&1 | grep -v 'file not found'
