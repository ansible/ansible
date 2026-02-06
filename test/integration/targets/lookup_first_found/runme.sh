#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ANSIBLE_LOOKUP_PLUGINS=. ansible-playbook runme.yml "$@"

ansible-playbook lookup_first_found_vars_files.yml -i inventory -v "$@"
