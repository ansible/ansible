#!/usr/bin/env bash

set -x

empty_limit_file="/tmp/limit_file"
touch "${empty_limit_file}"

cleanup() {
    if [[ -f "${empty_limit_file}" ]]; then
            rm -rf "${empty_limit_file}"
    fi
}

trap 'cleanup' EXIT

# https://github.com/ansible/ansible/issues/52152
# Ensure that non-matching limit causes failure with rc 1
ansible-playbook -i ../../inventory --limit foo playbook.yml
if [ "$?" != "1" ]; then
    echo "Non-matching limit should cause failure"
    exit 1
fi

# Ensure that non-matching limit causes failure with rc 1
ansible-playbook -i ../../inventory --limit @"${empty_limit_file}" playbook.yml

ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook -i ../../inventory "$@" strategy.yml
