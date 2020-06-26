#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook module_utils_basic_setcwd.yml -i ../../inventory "$@"

ansible-playbook module_utils_test.yml -i ../../inventory -v "$@"
ANSIBLE_MODULE_UTILS=other_mu_dir ansible-playbook module_utils_envvar.yml -i ../../inventory -v "$@"
