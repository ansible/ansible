#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

# Required to differentiate between Python 2 and 3 environ
PYTHON=${ANSIBLE_TEST_PYTHON_INTERPRETER:-python}

export ANSIBLE_CONFIG=ansible.cfg
export VMWARE_SERVER="${VCENTER_HOSTNAME}"
export VMWARE_USERNAME="${VCENTER_USERNAME}"
export VMWARE_PASSWORD="${VCENTER_PASSWORD}"
port=5000
VMWARE_CONFIG=test-config.vmware.yaml
inventory_cache="$(pwd)/inventory_cache"

cat > "$VMWARE_CONFIG" <<VMWARE_YAML
plugin: vmware_vm_inventory
strict: False
validate_certs: False
with_tags: False
VMWARE_YAML

cleanup() {
    echo "Cleanup"
    if [ -f "${VMWARE_CONFIG}" ]; then
        rm -f "${VMWARE_CONFIG}"
    fi
    if [ -d "${inventory_cache}" ]; then
        echo "Removing ${inventory_cache}"
        rm -rf "${inventory_cache}"
    fi
    echo "Done"
    exit 0
}

trap cleanup INT TERM EXIT

echo "DEBUG: Using ${VCENTER_HOSTNAME} with username ${VCENTER_USERNAME} and password ${VCENTER_PASSWORD}"

echo "Kill all previous instances"
curl "http://${VCENTER_HOSTNAME}:${port}/killall" > /dev/null 2>&1

echo "Start new VCSIM server"
curl "http://${VCENTER_HOSTNAME}:${port}/spawn?datacenter=1&cluster=1&folder=0" > /dev/null 2>&1

echo "Debugging new instances"
curl "http://${VCENTER_HOSTNAME}:${port}/govc_find"

# Get inventory
ansible-inventory -i ${VMWARE_CONFIG} --list

echo "Check if cache is working for inventory plugin"
if [ ! -n "$(find "${inventory_cache}" -maxdepth 1 -name 'vmware_vm_inventory_*' -print -quit)" ]; then
    echo "Cache directory not found. Please debug"
    exit 1
fi
echo "Cache is working"

# Get inventory using YAML
ansible-inventory -i ${VMWARE_CONFIG} --list --yaml

# Install TOML for --toml
${PYTHON} -m pip freeze | grep toml > /dev/null 2>&1
TOML_TEST_RESULT=$?
if [ $TOML_TEST_RESULT -ne 0 ]; then
    echo "Installing TOML package"
    ${PYTHON} -m pip install toml
else
    echo "TOML package already exists, skipping installation"
fi

# Get inventory using TOML
ansible-inventory -i ${VMWARE_CONFIG} --list --toml
TOML_INVENTORY_LIST_RESULT=$?
if [ $TOML_INVENTORY_LIST_RESULT -ne 0 ]; then
    echo "Inventory plugin failed to list inventory host using --toml, please debug"
    exit 1
fi

# Test playbook with given inventory
ansible-playbook -i ${VMWARE_CONFIG} test_vmware_vm_inventory.yml --connection=local "$@"
