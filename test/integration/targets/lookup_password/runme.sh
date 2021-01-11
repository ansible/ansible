#!/usr/bin/env bash

set -eux

export ANSIBLE_TEST_PREFER_VENV=1
source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml -e "output_dir=${OUTPUT_DIR}" "$@"
