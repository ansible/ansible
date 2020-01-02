#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install jinja2==2.11.0 jinja==2.11.0.dev0 --extra-index-url https://sivel.eng.ansible.com

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
