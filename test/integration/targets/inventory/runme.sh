#!/usr/bin/env bash

set -ux

# run multiple times to avoid coincidence of dict 'hashing' matching the order
for i in {1..5}
do
	ANSIBLE_YAML_ORDERED=1 ansible-playbook -i inv.yml test_ordered_yaml.yml -v "$@"
done
