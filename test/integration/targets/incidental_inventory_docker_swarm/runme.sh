#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

cleanup() {
    echo "Cleanup"
    ansible-playbook playbooks/swarm_cleanup.yml
    echo "Done"
}

trap cleanup INT TERM EXIT

echo "Setup"
ANSIBLE_ROLES_PATH=.. ansible-playbook  playbooks/swarm_setup.yml

echo "Test docker_swarm inventory 1"
ansible-playbook -i inventory_1.docker_swarm.yml playbooks/test_inventory_1.yml

echo "Test docker_swarm inventory 2"
ansible-playbook -i inventory_2.docker_swarm.yml playbooks/test_inventory_2.yml
