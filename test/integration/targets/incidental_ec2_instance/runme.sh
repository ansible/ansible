#!/usr/bin/env bash
#
# Beware: most of our tests here are run in parallel.
# To add new tests you'll need to add a new host to the inventory and a matching
# '{{ inventory_hostname }}'.yml file in roles/ec2_instance/tasks/


set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook main.yml -i inventory "$@"
