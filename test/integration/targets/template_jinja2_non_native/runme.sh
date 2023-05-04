#!/usr/bin/env bash

set -eux

export ANSIBLE_JINJA2_NATIVE=1
ansible-playbook 46169.yml -v "$@"
python -m pip install "Jinja2>=3.1.0"
ansible-playbook macro_override.yml -v "$@"
unset ANSIBLE_JINJA2_NATIVE
