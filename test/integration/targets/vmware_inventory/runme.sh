#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

# Get Current test directory
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

contrib_dir=$(pwd)/../../../../contrib/inventory
cd "${contrib_dir}"

if [ ! -f ./vmware_inventory.py ]; then
    echo "DEBUG: Unable to find vmware_inventory.py inside ${contrib_dir}"
    exit 1
fi

echo "DEBUG: using ${contrib_dir}"

export ANSIBLE_CONFIG=ansible.cfg
export vcenter_host="${vcenter_host:-0.0.0.0}"
export VMWARE_SERVER="${vcenter_host}"
export VMWARE_USERNAME="${VMWARE_USERNAME:-user}"
export VMWARE_PASSWORD="${VMWARE_PASSWORD:-pass}"

VMWARE_CONFIG=${contrib_dir}/vmware_inventory.ini
ANSIBLE_CFG=${contrib_dir}/ansible.cfg

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

cat > "${ANSIBLE_CFG}" << ANSIBLE_CFG_INI
[defaults]
ANSIBLE_CFG_INI

function cleanup {
    # Revert back to previous one
    if [ -f "${VMWARE_CONFIG}.bk" ]; then
        echo "DEBUG: Cleanup ${VMWARE_CONFIG}"
        mv "${VMWARE_CONFIG}.bk" "${VMWARE_CONFIG}"
    fi
        if [ -f "${ANSIBLE_CFG}" ]; then
        echo "DEBUG: Cleanup ${ANSIBLE_CFG}"
        rm "${ANSIBLE_CFG}"
    fi
}

echo "DEBUG: Using ${vcenter_host} with username ${VMWARE_USERNAME} and password ${VMWARE_PASSWORD}"

echo "Kill all previous instances"
curl "http://${vcenter_host}:5000/killall" > /dev/null 2>&1

echo "Start new VCSIM server"
curl "http://${vcenter_host}:5000/spawn?datacenter=1&cluster=1&folder=0" > /dev/null 2>&1

echo "Debugging new instances"
curl "http://${vcenter_host}:5000/govc_find"

# Get inventory
ansible-playbook -i ./vmware_inventory.py "${DIR}/test_vmware_inventory.yml" --connection=local "$@"

echo "DEBUG: Done"
