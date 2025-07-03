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

# Tests for MODULE_IGNORE_EXTS.
#
# Very similar to two tests above, but adds a check to test extension
# precedence. Separate from the above playbooks because we *only* care about
# extensions here and 'a' will not exist when the above playbooks run with
# non-extension library/role paths. There is also no way to guarantee that
# these tests will be useful due to how the pluginloader seems to work. It uses
# os.listdir which returns things in an arbitrary order (likely dependent on
# filesystem). If it happens to return 'a.py' on the test node before it
# returns 'a.ini', then this test is pointless anyway because there's no chance
# that 'a.ini' would ever have run regardless of what MODULE_IGNORE_EXTS is set
# to. The hope is that we test across enough systems that one would fail this
# test if the MODULE_IGNORE_EXTS broke, but there is no guarantee. This would
# perhaps be better as a mocked unit test because of this but would require
# a fair bit of work to be feasible as none of that loader logic is tested at
# all right now.
ANSIBLE_LIBRARY=lib_with_extension ansible-playbook modules_test_envvar_ext.yml -i ../../inventory -v "$@"
ANSIBLE_ROLES_PATH=roles_with_extension ansible-playbook modules_test_role_ext.yml -i ../../inventory -v "$@"
