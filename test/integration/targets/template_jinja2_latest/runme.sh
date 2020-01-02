#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install -U https://github.com/pallets/jinja/tarball/the-great-rename

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
