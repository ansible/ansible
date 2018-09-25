#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

export ANSIBLE_CONFIG=ansible.cfg
export vcenter_host="${vcenter_host:-0.0.0.0}"
export VMWARE_SERVER="${vcenter_host}"
export VMWARE_USERNAME="${VMWARE_USERNAME:-user}"
export VMWARE_PASSWORD="${VMWARE_PASSWORD:-pass}"
VMWARE_CONFIG=test-config.vmware.yaml

cat > "$VMWARE_CONFIG" <<VMWARE_YAML
plugin: vmware_vm_inventory
strict: False
validate_certs: False
with_tags: False
VMWARE_YAML

trap 'rm -f "${VMWARE_CONFIG}"' INT TERM EXIT

echo "DEBUG: Using ${vcenter_host} with username ${VMWARE_USERNAME} and password ${VMWARE_PASSWORD}"

echo "Kill all previous instances"
curl "http://${vcenter_host}:5000/killall" > /dev/null 2>&1

echo "Start new VCSIM server"
curl "http://${vcenter_host}:5000/spawn?datacenter=1&cluster=1&folder=0" > /dev/null 2>&1

echo "Debugging new instances"
curl "http://${vcenter_host}:5000/govc_find"

# Get inventory
ansible-inventory -i ${VMWARE_CONFIG} --list
# Test playbook with given inventory
ansible-playbook -i ${VMWARE_CONFIG} test_vmware_vm_inventory.yml --connection=local "$@"
