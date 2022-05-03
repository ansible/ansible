#!/usr/bin/env bash

set -eux

export ANSIBLE_FORCE_COLOR=0
export ANSIBLE_DEPRECATION_WARNINGS=1

ansible-playbook block_vars.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook import_tasks.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook include_role.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook include_tasks.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook include_vars.yml "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -i inventory_invalid_host_vars/inventory host1 "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -i inventory_invalid_host_vars_file/inventory host1 "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -i inventory_invalid_group_vars/inventory host1 "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -i inventory_invalid_group_vars_file/inventory host1 "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook play_vars.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook register.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook roles-defaults.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook roles-vars.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook roles.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook set_fact.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook set_stats.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook task_vars.yml "$@" 2>&1 | grep "Invalid variable name"
ansible-playbook vars_files.yml "$@" 2>&1 | grep "Invalid variable name"

ansible -m debug -e 'lookup=ansible_jinja_global' localhost "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'lipsum=jinja_global' localhost "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'name=attribute' localhost "$@" 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'loop_with=private_attribute' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'def=python_keyword' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'ansible=ansible_keyword' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'to_nice_json=ansible_filter' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'truthy=ansible_test' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'with_items=with_lookup' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'fileglob=lookup' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'selectattr=jinja_filter' localhost 2>&1 | grep "Invalid variable name"
ansible -m debug -e 'defined=jinja_test' localhost 2>&1 | grep "Invalid variable name"
