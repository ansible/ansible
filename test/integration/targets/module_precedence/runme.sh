#!/usr/bin/env bash

set -eux

# Standard ping module
ansible-playbook modules_test.yml -i ../../inventory -v "$@"

# Library path ping module
ANSIBLE_LIBRARY=lib_with_extension ansible-playbook modules_test_envvar.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_no_extension ansible-playbook modules_test_envvar.yml -i ../../inventory -v "$@"

# ping module from role
ANSIBLE_ROLES_PATH=roles_with_extension ansible-playbook modules_test_role.yml -i ../../inventory -v "$@"
ANSIBLE_ROLES_PATH=roles_no_extension ansible-playbook modules_test_role.yml -i ../../inventory -v "$@"

# ping module from role when there's a library path module too
ANSIBLE_LIBRARY=lib_no_extension ANSIBLE_ROLES_PATH=roles_with_extension ansible-playbook modules_test_role.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_with_extension ANSIBLE_ROLES_PATH=roles_with_extension ansible-playbook modules_test_role.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_no_extension ANSIBLE_ROLES_PATH=roles_no_extension ansible-playbook modules_test_role.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_with_extension ANSIBLE_ROLES_PATH=roles_no_extension ansible-playbook modules_test_role.yml -i ../../inventory -v "$@"

# ping module in multiple roles: Note that this will use the first module found
# which is the current way things work but may not be the best way
ANSIBLE_LIBRARY=lib_no_extension ANSIBLE_ROLES_PATH=multiple_roles ansible-playbook modules_test_multiple_roles.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_with_extension ANSIBLE_ROLES_PATH=multiple_roles ansible-playbook modules_test_multiple_roles.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_no_extension ANSIBLE_ROLES_PATH=multiple_roles ansible-playbook modules_test_multiple_roles.yml -i ../../inventory -v "$@"
ANSIBLE_LIBRARY=lib_with_extension ANSIBLE_ROLES_PATH=multiple_roles ansible-playbook modules_test_multiple_roles.yml -i ../../inventory -v "$@"

# And prove that with multiple roles, it's the order the roles are listed in the play that matters
ANSIBLE_LIBRARY=lib_with_extension ANSIBLE_ROLES_PATH=multiple_roles ansible-playbook modules_test_multiple_roles_reverse_order.yml -i ../../inventory -v "$@"
