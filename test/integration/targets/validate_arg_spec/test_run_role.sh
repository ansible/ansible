#!/bin/bash

# ANSIBLE_ROLES_PATH=../ ansible-playbook -i ../../inventory -e @../../integration_config.yml -vvv test.yml
ANSIBLE_PLAYBOOK=${ANSIBLE_PLAYBOOK:-"ansible-playbook"}
"$ANSIBLE_PLAYBOOK" -i ../../inventory -e @../../integration_config.yml -e@validate_extra_vars.yml -vvvv run_role.yml
