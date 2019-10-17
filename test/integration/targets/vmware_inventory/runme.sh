#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

contrib_dir=../../../../contrib/inventory

echo "DEBUG: using ${contrib_dir}"

export ANSIBLE_CONFIG=ansible.cfg
export VMWARE_SERVER="${VCENTER_HOSTNAME}"
export VMWARE_USERNAME="${VCENTER_USERNAME}"
export VMWARE_PASSWORD="${VCENTER_PASSWORD}"

VMWARE_CONFIG=${contrib_dir}/vmware_inventory.ini


trap cleanup INT TERM EXIT

# Remove default inventory config file
if [ -f "${VMWARE_CONFIG}" ];
then
    echo "DEBUG: Creating backup of ${VMWARE_CONFIG}"
    cp "${VMWARE_CONFIG}" "${VMWARE_CONFIG}.bk"
fi

cat > "${VMWARE_CONFIG}" <<VMWARE_INI
[vmware]
server=${VMWARE_SERVER}
username=${VMWARE_USERNAME}
password=${VMWARE_PASSWORD}
validate_certs=False
VMWARE_INI

function cleanup {
    # Revert back to previous one
    if [ -f "${VMWARE_CONFIG}.bk" ]; then
        echo "DEBUG: Cleanup ${VMWARE_CONFIG}"
        mv "${VMWARE_CONFIG}.bk" "${VMWARE_CONFIG}"
    fi
}

echo "DEBUG: Using ${VCENTER_HOSTNAME} with username ${VCENTER_USERNAME} and password ${VCENTER_PASSWORD}"

echo "Kill all previous instances"
curl "http://${VCENTER_HOSTNAME}:5000/killall" > /dev/null 2>&1

echo "Start new VCSIM server"
curl "http://${VCENTER_HOSTNAME}:5000/spawn?datacenter=1&cluster=1&folder=0" > /dev/null 2>&1

echo "Debugging new instances"
curl "http://${VCENTER_HOSTNAME}:5000/govc_find"

# Get inventory
ansible-playbook -i ./vmware_inventory.sh "./test_vmware_inventory.yml" --connection=local "$@"

echo "DEBUG: Done"
