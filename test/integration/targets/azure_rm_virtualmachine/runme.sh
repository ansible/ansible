#!/usr/bin/env bash

set -eux

# Add -vvv for detailed output if your tests are failing as:
ansible-playbook main.yaml -i inventory "$@"
