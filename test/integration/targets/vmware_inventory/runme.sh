#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

export ANSIBLE_CONFIG=ansible.cfg
export vcenter_host="${vcenter_host:-0.0.0.0}"
export vcenter_user="${vcenter_user:-user}"
export vcenter_pass="${vcenter_pass:-pass}"
VMWARE_CONFIG=test-config.vmware.yaml

# flag for checking whether cleanup has already fired
_is_clean=

function _cleanup() {
    [[ -n "$_is_clean" ]] && return  # don't double-clean
    echo Cleanup: removing ${VMWARE_CONFIG}...
    rm -vf "$VMWARE_CONFIG"
    unset ANSIBLE_CONFIG
    unset vcenter_host
    unset vcenter_user
    unset vcenter_pass
    unset VMWARE_CONFIG
    _is_clean=1
}
trap _cleanup INT TERM EXIT

cat > "$VMWARE_CONFIG" <<VMWARE_YAML
plugin: vmware_inventory
strict: False
hostname: ${vcenter_host}
username: ${vcenter_user}
password: ${vcenter_pass}
validate_certs: False
with_tags: False
VMWARE_YAML

echo "Installing Pyvmomi"
pip install pyvmomi
pip2 install pyvmomi

echo "Kill all previous instances"
curl "http://${vcenter_host}:5000/killall" > /dev/null 2>&1

echo "Start new VCSIM server"
curl "http://${vcenter_host}:5000/spawn?datacenter=1&cluster=1&folder=0" > /dev/null 2>&1

echo "Debugging new instances"
curl "http://${vcenter_host}:5000/govc_find"

# Get inventory
ansible-inventory -i ${VMWARE_CONFIG} --list
# Test playbook with given inventory
ansible-playbook -i ${VMWARE_CONFIG} test_vmware_inventory.yml --connection=local "$@"
