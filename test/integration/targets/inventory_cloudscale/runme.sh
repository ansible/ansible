#!/bin/sh

# Exit on errors, exit when accessing unset variables and print all commands
set -eux

# Set the role path so that the cloudscale_common role is available
export ANSIBLE_ROLES_PATH="../"

# Set the filter plugin search path so that the safe_group_name filter is available
export ANSIBLE_FILTER_PLUGINS="./filter_plugins"

rm -f inventory.yml
export ANSIBLE_INVENTORY="./inventory_cloudscale.yml"

# Run without converting invalid characters in group names
export ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never
ansible-playbook playbooks/test-inventory.yml "$@"

# Run with converting invalid characters in group names
export ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always
ansible-playbook playbooks/test-inventory.yml "$@"
