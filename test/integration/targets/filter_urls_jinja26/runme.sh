#!/usr/bin/env bash

set -eux

source virtualenv.sh

# This has to be done outside of requirements.txt but is necessary for
# installing Jinja 2.6
pip install 'setuptools<45'

pip install -U -r requirements.txt

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
