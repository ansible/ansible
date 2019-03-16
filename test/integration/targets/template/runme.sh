#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook template.yml -i ../../inventory -e @../../integration_config.yml -v "$@"

# Test for #35571
ansible testhost -i testhost, -m debug -a 'msg={{ hostvars["localhost"] }}' -e "vars1={{ undef }}" -e "vars2={{ vars1 }}"

# Test for https://github.com/ansible/ansible/issues/27262
ansible-playbook ansible_managed.yml -c  ansible_managed.cfg -i ../../inventory -e @../../integration_config.yml -v "$@"

# Test for #42585
ANSIBLE_ROLES_PATH=../ ansible-playbook custom_template.yml -i ../../inventory -e @../../integration_config.yml -v "$@"
