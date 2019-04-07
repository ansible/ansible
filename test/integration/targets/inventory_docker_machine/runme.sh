#!/usr/bin/env bash
# set DIGITALOCEAN_TOKEN to your Digital Ocean API token before running this test
DM_MACHINE_NAME="dm-inventory-test"

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

cleanup() {
    echo "Cleanup"
    docker-machine rm --force ${DM_MACHINE_NAME}
    echo "Done"
    exit 0
}

trap cleanup INT TERM EXIT

echo "Setup"
docker-machine create \
        --driver digitalocean \
        --digitalocean-access-token ${DIGITALOCEAN_TOKEN} \
        --digitalocean-region ams3 \
        --digitalocean-image ubuntu-18-04-x64 \
        --digitalocean-size s-1vcpu-1gb \
        --digitalocean-tags sometag:somevalue,othertag:othervalue \
        ${DM_MACHINE_NAME}

echo "Test docker_machine inventory 1"
ansible-playbook -i inventory_1.docker_machine.yml playbooks/test_inventory_1.yml
