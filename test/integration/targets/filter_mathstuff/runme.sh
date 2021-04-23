#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook runme.yml "$@"

source virtualenv.sh

# Install Jinja < 2.10 since we want to test the fallback to Ansible's custom
# unique filter. Jinja < 2.10 does not have do_unique so we will trigger the
# fallback.
pip install 'jinja2 < 2.10'

# Run the playbook again in the venv with Jinja < 2.10
ansible-playbook runme.yml "$@"
