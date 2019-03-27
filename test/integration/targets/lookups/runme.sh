#!/usr/bin/env bash

set -ex
virtualenv --system-site-packages --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${OUTPUT_DIR}/venv"
source "${OUTPUT_DIR}/venv/bin/activate"
set -eux

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook lookups.yml -i ../../inventory -e @../../integration_config.yml "$@"

ansible-playbook template_lookup_vaulted.yml -i ../../inventory -e @../../integration_config.yml --vault-password-file test_vault_pass "$@"
