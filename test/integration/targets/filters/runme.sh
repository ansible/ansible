#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

pip install jmespath netaddr bcrypt passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml "$@"
