#!/usr/bin/env bash
# set DIGITALOCEAN_TOKEN to your Digital Ocean API token before running this test

SCRIPT_DIR=$(dirname "$0")
export DM_MACHINE_NAME=dm-test-machine-${RANDOM}

# restrict Ansible just to our inventory plugin, to prevent inventory data being matched by the test but being provided
# by some other dynamic inventory provider
export ANSIBLE_INVENTORY_ENABLED=docker_machine

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

cleanup() {
    echo "Cleanup"
    ansible-playbook -i teardown.docker_machine.yml playbooks/teardown.yml
    echo "Done"
    exit 0
}

trap cleanup INT TERM EXIT

echo "Check preconditions"
# Host should NOT be known to Ansible before the test starts
ansible-inventory -i inventory_1.docker_machine.yml --host ${DM_MACHINE_NAME} >/dev/null && exit 1

echo "Test that the docker_machine inventory plugin is being loaded"
ANSIBLE_DEBUG=yes ansible-inventory -i inventory_1.docker_machine.yml --list | grep -F "Loading InventoryModule 'docker_machine'"

echo "Setup"
ansible-playbook -i inventory_1.docker_machine.yml playbooks/setup.yml

echo "Test docker_machine inventory 1"
ansible-playbook -i inventory_1.docker_machine.yml playbooks/test_inventory_1.yml

echo "Activate Docker Machine mock"
SAVED_PATH=$PATH
PATH=${SCRIPT_DIR}:$PATH

echo "Test docker_machine inventory 2: daemon_required=yes daemon env success=yes"
ansible-inventory -i inventory_2.docker_machine.yml --list

echo "Test docker_machine inventory 2: daemon_required=yes daemon env success=no"
export MOCK_ERROR_IN=env
ansible-inventory -i inventory_2.docker_machine.yml --list
unset MOCK_ERROR_IN

echo "Test docker_machine inventory 3: daemon_required=no daemon env success=yes"
ansible-inventory -i inventory_3.docker_machine.yml --list

echo "Test docker_machine inventory 3: daemon_required=no daemon env success=no"
export MOCK_ERROR_IN=env
ansible-inventory -i inventory_2.docker_machine.yml --list
unset MOCK_ERROR_IN

echo "Deactivate Docker Machine mock"
PATH=${SAVED_PATH}
