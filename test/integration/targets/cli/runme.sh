#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook setup.yml

python test-cli.py
python test_k_and_K.py
