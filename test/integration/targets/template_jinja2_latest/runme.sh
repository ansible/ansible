#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install -U https://github.com/pallets/jinja/tarball/the-great-rename
pip install -U 'https://github.com/pallets/jinja/tarball/the-great-rename#egg=jinja2&subdirectory=jinja2-compat'

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
