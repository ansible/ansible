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

# Ensure that non-existing limit file causes failure with rc 1
ansible-playbook -i ../../inventory --limit @foo playbook.yml
if [ "$?" != "1" ]; then
    echo "Non-existing limit file should cause failure"
    exit 1
fi

# Ensure that non-matching limit causes failure with rc 1
ansible-playbook -i ../../inventory --limit @"${empty_limit_file}" playbook.yml

ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook -i ../../inventory "$@" strategy.yml

# test extra vars
ansible-inventory -i testhost, -i ./extra_vars_constructed.yml --list -e 'from_extras=hey ' "$@"|grep '"example": "hellohey"'

# test parse inventory fail is not an error per config
ANSIBLE_INVENTORY_UNPARSED_FAILED=False ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False ansible -m ping localhost -i /idontexist "$@"

# test no inventory parse is an error with var
[ "$(ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False ansible -m ping localhost -i /idontexist)" != "0" ]

# test single inventory no parse is not an error with var
ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False ansible -m ping localhost -i /idontexist -i ../../invenotory "$@"

# test single inventory no parse is an error with any var
[ "$(ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=True ansible -m ping localhost -i /idontexist -i ../../invenotory)" != "0" ]
