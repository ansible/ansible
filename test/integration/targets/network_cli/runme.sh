#!/usr/bin/env bash
set -ux # no -e because we want to run teardown no matter waht
export ANSIBLE_ROLES_PATH=../

ansible-playbook setup.yml -i $INVENTORY_PATH "$@"

# We need a nonempty file to override key with (empty file gives a
# lovely "list index out of range" error)
foo=`mktemp`
echo hello > $foo

ansible-playbook \
    -i $INVENTORY_PATH \
    -e ansible_user=atester \
    -e ansible_password=testymctest \
    -e ansible_ssh_private_key_file=$foo \
    passworded_user.yml

ansible-playbook teardown.yml -i $INVENTORY_PATH "$@"
