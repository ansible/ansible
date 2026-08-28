#!/usr/bin/env bash

set -eux -o pipefail

ANSIBLE_ROLES_PATH=../ ansible-playbook setup.yml
python ask_pass.py
