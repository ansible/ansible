#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook module_utils_basic_setcwd.yml -i ../../inventory "$@"

# Keep the -vvvvv here. This acts as a test for testing that higher verbosity
# doesn't traceback with unicode in the custom module_utils directory path.
ansible-playbook module_utils_vvvvv.yml -i ../../inventory -vvvvv "$@"

ansible-playbook module_utils_test.yml -i ../../inventory -v "$@"

ANSIBLE_MODULE_UTILS=other_mu_dir ansible-playbook module_utils_envvar.yml -i ../../inventory -v "$@"

ansible-playbook module_utils_common_dict_transformation.yml -i ../../inventory "$@"

ansible-playbook module_utils_common_network.yml -i ../../inventory "$@"

ansible-playbook module_utils_basic_invocation.yml "$@"

export ANSIBLE_LIBRARY=library ANSIBLE_DEPRECATION_WARNINGS=True
deprecation="\[DEPRECATION WARNING\]: Inferring a task failure from a non-zero \`rc\` is deprecated"

ansible localhost -m test_rc "$@" && exit 1 || echo 'Task failed as expected'
ansible localhost -m test_rc "$@" 2>&1 | grep "$deprecation"
[ "$(ansible localhost -m test_rc -a failed=True "$@" 2>&1 | grep -c "$deprecation")" -eq 0 ]
[ "$(ansible localhost -m test_rc -a failed=False "$@" 2>&1 | grep -c "$deprecation")" -eq 0 ]
