#!/usr/bin/env bash

set -eux

ansible-playbook -i inventory.ini test_types.yml "${@}"
ansible-playbook -v -i inventory.ini test_ansible_become.yml

ansible-inventory -v -i inventory.ini --list 2> out
test "$(grep -c 'SyntaxWarning' out)" -eq 0
