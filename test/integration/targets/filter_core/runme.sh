#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml "$@"
ANSIBLE_ROLES_PATH=../ ansible-playbook handle_undefined_type_errors.yml "$@"

# Remove passlib installed by setup_passlib_controller
source virtualenv.sh
SITE_PACKAGES=$(python -c "import sysconfig; print(sysconfig.get_path('purelib'))")
echo "raise ImportError('passlib')" > "${SITE_PACKAGES}/passlib.py"
ANSIBLE_ROLES_PATH=../ ansible-playbook password_hash.yml "$@"
