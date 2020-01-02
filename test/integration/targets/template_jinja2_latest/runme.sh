#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install -U git+https://github.com/pallets/jinja.git@the-great-rename

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
