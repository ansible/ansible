#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install --requirement pip-requirements.txt

pip install -U -r requirements.txt --constraint "../../../lib/ansible_test/_data/requirements/constraints.txt"

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
