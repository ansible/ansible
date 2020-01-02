#!/usr/bin/env bash

set -eux

source virtualenv.sh

PY_VER=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

if [ "$PY_VER" == "2.6" ]; then
    pip install -U jinja2
else
    pip install --extra-index-url https://sivel.eng.ansible.com/pypi/ --no-binary jinja,jinja2 jinja2==2.11.0 jinja==2.11.0.dev0
fi

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -v "$@"
