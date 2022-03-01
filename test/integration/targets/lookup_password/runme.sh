#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib cryptography jinja2 PyYAML

ANSIBLE_VAULT_PASSWORD_FILE=vault_password.txt ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml -e "output_dir=${OUTPUT_DIR}" "$@"
