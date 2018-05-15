#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

export ANSIBLE_CONFIG=ansible.cfg
export vcenter_host="${vcenter_host:-0.0.0.0}"
export vcenter_user="${vcenter_user:-user}"
export vcenter_pass="${vcenter_pass:-pass}"
VMWARE_CONFIG=test-config.vmware.yaml

cat > "$VMWARE_CONFIG" <<VMWARE_YAML
plugin: vmware_inventory
strict: False
hostname: ${vcenter_host}
username: ${vcenter_user}
password: ${vcenter_pass}
validate_certs: False
with_tags: False
VMWARE_YAML

trap 'rm -f "${VMWARE_CONFIG}"' INT TERM EXIT

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
