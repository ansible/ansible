#!/usr/bin/env bash

source virtualenv.sh

set -eux

# remove `*.py` scripts from the venv to avoid attempts to load them as plugins
rm -f "${OUTPUT_DIR}"/venv/bin/*.py

ANSIBLE_ROLES_PATH=../ ansible-playbook test.yml -i inventory "$@"
