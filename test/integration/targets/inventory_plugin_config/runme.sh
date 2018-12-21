#!/usr/bin/env bash

set -o errexit -o nounset -o xtrace

export ANSIBLE_INVENTORY_PLUGINS=./
export ANSIBLE_INVENTORY_ENABLED=test_inventory

# check default values
ansible-inventory --list -i ./config_without_parameter.yml --export | \
    env python -c "import json, sys; inv = json.loads(sys.stdin.read()); \
                   assert set(inv['_meta']['hostvars']['test_host']['departments']) == set(['seine-et-marne', 'haute-garonne'])"

# check values
ansible-inventory --list -i ./config_with_parameter.yml --export | \
    env python -c "import json, sys; inv = json.loads(sys.stdin.read()); \
                   assert set(inv['_meta']['hostvars']['test_host']['departments']) == set(['paris'])"
