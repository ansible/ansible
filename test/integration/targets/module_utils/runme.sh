#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook module_utils_basic_setcwd.yml -i ../../inventory "$@"

# Keep the -vvvvv here. This acts as a test for testing that higher verbosity
# doesn't traceback with unicode in the custom module_utils directory path.
ansible-playbook module_utils_vvvvv.yml -i ../../inventory -vvvvv "$@"

ansible-playbook module_utils_test.yml -i ../../inventory -v "$@"
ANSIBLE_MODULE_UTILS=other_mu_dir ansible-playbook module_utils_envvar.yml -i ../../inventory -v "$@"

ansible-playbook module_utils_common_dict_transformation.yml -i ../../inventory "$@"
