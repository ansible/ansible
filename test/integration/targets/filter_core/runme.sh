#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml "$@"
ANSIBLE_ROLES_PATH=../ ansible-playbook handle_undefined_type_errors.yml "$@"
