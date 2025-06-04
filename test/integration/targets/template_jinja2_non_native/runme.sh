#!/usr/bin/env bash

set -eux

ansible-playbook 46169.yml -v "$@"
python -m pip install "Jinja2>=3.1.0"
ansible-playbook macro_override.yml -v "$@"
