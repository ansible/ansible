#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook setup.yml

python test-cli.py

ansible-playbook test_syntax/syntax_check.yml --syntax-check -i ../../inventory -v "$@"
