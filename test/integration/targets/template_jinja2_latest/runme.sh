#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install -U jinja2

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -e @../../integration_config.yml -v "$@"
