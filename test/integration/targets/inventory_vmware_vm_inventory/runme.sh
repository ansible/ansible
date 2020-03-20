#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

# Required to differentiate between Python 2 and 3 environ
export ANSIBLE_PYTHON_INTERPRETER=${ANSIBLE_TEST_PYTHON_INTERPRETER:-$(which python)}

# prepare_vmware_test envs!
export VMWARE_HOST="${VCENTER_HOSTNAME}"
export VMWARE_USER="${VCENTER_USERNAME}"
export VMWARE_PASSWORD="${VCENTER_PASSWORD}"
export VMWARE_VALIDATE_CERTS="no" # Note: Should be set by ansible-test

cleanup() {
    ec=$?
    inventory_cache="inventory_cache"
    echo "Cleanup"
    if [ -d "${inventory_cache}" ]; then
        echo "Removing ${inventory_cache}"
        rm -rf "${inventory_cache}"
    fi
    echo "Done"
    exit $ec
}
trap cleanup INT TERM EXIT

set_inventory(){
    export ANSIBLE_INVENTORY="${1}"
    echo "INVENTORY '${1}' is active" 
}


# Install dependencies
ansible-playbook -i 'localhost,' playbook/install_dependencies.yaml "$@"

# Prepare tests
ansible-playbook -i 'localhost,' playbook/prepare_vmware.yaml "$@"


set_inventory "inventory/defaults_with_cache.vmware.yaml"
# Get inventory
ansible-inventory --list 1>/dev/null

# Check if cache is working for inventory plugin
ansible-playbook playbook/test_inventory_cache.yml "$@"

# Get inventory using YAML
ansible-inventory --list --yaml 1>/dev/null

# Get inventory using TOML
ansible-inventory --list --toml 1>/dev/null


set_inventory "inventory/defaults.vmware.yaml"
# Test playbook with given inventory
ansible-playbook playbook/test_vmware_vm_inventory.yml "$@"