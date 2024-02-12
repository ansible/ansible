#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml "$@"
ANSIBLE_ROLES_PATH=../ ansible-playbook handle_undefined_type_errors.yml "$@"

# Remove passlib installed by setup_passlib_controller
python -m pip uninstall -y passlib
ANSIBLE_ROLES_PATH=../ ansible-playbook password_hash.yml "$@"
