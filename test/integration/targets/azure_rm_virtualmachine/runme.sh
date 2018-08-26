#!/usr/bin/env bash

set -eux

# Add -vvv for detailed output if your tests are failing as:
#ansible-playbook -vvv main.yaml -i inventory "$@"
ansible-playbook main.yaml -i inventory "$@"