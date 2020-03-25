#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook runme.yml "$@"

source virtualenv.sh

# This has to be done outside of requirements.txt but is necessary for
# installing Jinja 2.6. We need this because Jinja 2.6 won't install with
# a newer setuptools, and because setuptools 45+ won't work with Python 2.
pip install 'setuptools<45'

pip install -U -r requirements.txt

# Run the playbook again in the venv with Jinja 2.6
ansible-playbook runme.yml "$@"
