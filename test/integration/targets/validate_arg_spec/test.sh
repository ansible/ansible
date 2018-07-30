#!/bin/bash

ANSIBLE_PLAYBOOK=ansible-playbook-alog
ANSIBLE_ROLES_PATH=../ "$ANSIBLE_PLAYBOOK" -i ../../inventory -e @../../integration_config.yml -vvv test.yml

