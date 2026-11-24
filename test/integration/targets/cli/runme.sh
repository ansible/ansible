#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook setup.yml

python test-cli.py

ansible-playbook test_syntax/syntax_check.yml --syntax-check -i ../../inventory -v "$@"

ansible-playbook test_syntax/module_path_check.yml --syntax-check -i ../../inventory -M ./custom_module_path/library -v "$@"
ansible-playbook test_syntax/module_path_check.yml --syntax-check -i ../../inventory --module-path ./custom_module_path/library -v "$@"

ansible-playbook test_syntax/module_path_check.yml --list-tasks -i ../../inventory -M ./custom_module_path/library -v "$@"
ansible-playbook test_syntax/module_path_check.yml --list-tasks -i ../../inventory --module-path ./custom_module_path/library -v "$@"
