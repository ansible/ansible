#!/usr/bin/env bash

set -eux

# creates the test inventory file based on the user's inventory.winrm file
ansible-playbook setup.yml -i ../../inventory.winrm "$@"

# runs the tests
ansible-playbook main.yml -i inventory.ini "$@"

# remove test inventory file at the end
rm inventory.ini
