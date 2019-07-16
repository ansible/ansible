#!/usr/bin/env bash

set -x

# https://github.com/ansible/ansible/issues/52152
# Ensure that non-matching limit causes failure with rc 1
ansible-playbook -i ../../inventory --limit foo playbook.yml
if [ "$?" != "1" ]; then
    echo "Non-matching limit should cause failure"
    exit 1
fi

ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook -i ../../inventory "$@" strategy.yml
