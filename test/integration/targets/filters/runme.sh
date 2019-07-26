#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

pip install --no-build-isolation bcrypt
pip install jmespath netaddr passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml "$@"
