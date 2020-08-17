#!/usr/bin/env bash
set -eux
export ANSIBLE_ROLES_PATH=../

function cleanup {
    ansible-playbook teardown.yml -i "$INVENTORY_PATH" "$@"
}

trap cleanup EXIT

ansible-playbook setup.yml -i "$INVENTORY_PATH" "$@"

# We need a nonempty file to override key with (empty file gives a
# lovely "list index out of range" error)
foo=$(mktemp)
echo hello > "$foo"

# We want to ensure that passwords make it to the network connection plugins
# because they follow a different path than the rest of the codebase.
# In setup.yml, we create a passworded user, and now we connect as that user
# to make sure the password we pass here successfully makes it to the plugin.
ansible-playbook \
    -i "$INVENTORY_PATH" \
    -e ansible_user=atester \
    -e ansible_password=testymctest \
    -e ansible_ssh_private_key_file="$foo" \
    passworded_user.yml
