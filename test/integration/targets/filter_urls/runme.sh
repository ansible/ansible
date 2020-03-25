#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook runme.yml "$@"

source virtualenv.sh

# This is necessary for installing Jinja 2.6. We need this because Jinja 2.6
# won't install with newer setuptools, and because setuptools 45+ won't work
# with Python 2.
pip install 'setuptools<45'

# Install Jinja 2.6 since we want to test the fallback to Ansible's custom
# urlencode functions. Jinja 2.6 does not have urlencode so we will trigger the
# fallback.
pip install 'jinja2 >= 2.6, < 2.7'

# Run the playbook again in the venv with Jinja 2.6
ansible-playbook runme.yml "$@"
