#!/usr/bin/env bash
# set DIGITALOCEAN_TOKEN to your Digital Ocean API token before running this test

export DM_MACHINE_NAME=dm-test-machine

# restrict Ansible just to our inventory plugin, to prevent inventory data being matched by the test but being provided
# by some other dynamic inventory provider
export ANSIBLE_INVENTORY_ENABLED=docker_machine

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

cleanup() {
    echo "Cleanup"
    ansible-playbook -i inventory_1.docker_machine.yml playbooks/teardown.yml
    echo "Done"
    exit 0
}

trap cleanup INT TERM EXIT

echo "Check preconditions"
# Host should NOT be known to Ansible before the test starts
! ansible-inventory -i inventory_1.docker_machine.yml --list --host ${DM_MACHINE_NAME}

echo "Test that the docker_machine inventory plugin is being loaded"
ANSIBLE_DEBUG=yes ansible-inventory -i inventory_1.docker_machine.yml --list >/dev/null | grep -Fq "Loading InventoryModule 'docker_machine'"

echo "Setup"
ansible-playbook -i inventory_1.docker_machine.yml playbooks/setup.yml

echo "Test docker_machine inventory 1"
ansible-playbook -i inventory_1.docker_machine.yml playbooks/test_inventory_1.yml

