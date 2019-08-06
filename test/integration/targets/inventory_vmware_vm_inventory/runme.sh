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
    echo "Cleanup: Starting"
    if [ -f "${VMWARE_CONFIG}" ]; then
        rm -f "${VMWARE_CONFIG}"
    fi
    if [ -d "${inventory_cache}" ]; then
        echo "Removing ${inventory_cache}"
        rm -rf "${inventory_cache}"
    fi
    echo "Cleanup: Done"
}

# This is required, as otherwise we overwite exit codes of commands we call and the integration
# test fails prematurely, but reports successful execution
failure_cleanup() {
    echo "Previous command faild."
    cleanup
    exit 1
}

# Register a exception handler to perform a cleanup after one of the following commands fails
# and exit with exit code 1
trap failure_cleanup INT TERM
# Register a handler for the Exit event (the script finished execution normally or exit was called)
# to perform a cleanup
trap cleanup EXIT

echo "DEBUG: Using ${VCENTER_HOSTNAME} with username ${VCENTER_USERNAME} and password ${VCENTER_PASSWORD}"

echo "Kill all previous instances"
curl "http://${VCENTER_HOSTNAME}:${port}/killall" > /dev/null 2>&1

echo "Start new VCSIM server"
curl "http://${VCENTER_HOSTNAME}:${port}/spawn?datacenter=1&cluster=1&folder=0" > /dev/null 2>&1

echo "Debugging new instances"
curl "http://${VCENTER_HOSTNAME}:${port}/govc_find"

echo "Creates folder structure to test inventory folder support"
ansible-playbook -i 'localhost,' test_vmware_prep_folders.yml

echo "Get inventory"
ansible-inventory -i ${VMWARE_CONFIG} --list

echo "Check if cache is working for inventory plugin"
if [ ! -n "$(find "${inventory_cache}" -maxdepth 1 -name 'vmware_vm_inventory_*' -print -quit)" ]; then
    echo "Cache directory not found. Please debug"
    exit 1
fi
echo "Cache is working"

echo "Get inventory using YAML"
ansible-inventory -i ${VMWARE_CONFIG} --list --yaml

echo "Install TOML for --toml"
${PYTHON} -m pip freeze | grep toml > /dev/null 2>&1
TOML_TEST_RESULT=$?
if [ $TOML_TEST_RESULT -ne 0 ]; then
    echo "Installing TOML package"
    ${PYTHON} -m pip install toml
else
    echo "TOML package already exists, skipping installation"
fi

echo "Get inventory using TOML"
ansible-inventory -i ${VMWARE_CONFIG} --list --toml
TOML_INVENTORY_LIST_RESULT=$?
if [ $TOML_INVENTORY_LIST_RESULT -ne 0 ]; then
    echo "Inventory plugin failed to list inventory host using --toml, please debug"
    exit 1
fi

echo "Test playbook with given inventory"
ansible-playbook -i ${VMWARE_CONFIG} test_vmware_vm_inventory.yml --connection=local "$@"
