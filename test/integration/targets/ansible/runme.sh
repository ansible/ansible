#!/usr/bin/env bash

set -eux -o pipefail

ansible --version
ansible --help

ansible testhost -i ../../inventory -m ping  "$@"
ansible testhost -i ../../inventory -m setup "$@"

ansible-config -c ./ansible-testé.cfg view | grep 'remote_user = admin'
ansible-config -c ./ansible-testé.cfg dump | grep 'DEFAULT_REMOTE_USER([^)]*) = admin\>'
ANSIBLE_REMOTE_USER=administrator ansible-config dump| grep 'DEFAULT_REMOTE_USER([^)]*) = administrator\>'
ansible-config list | grep 'DEFAULT_REMOTE_USER'

# 'view' command must fail when config file is missing
ansible-config -c ./ansible-non-existent.cfg view && exit 1 || echo 'Failure is expected'

################################################################################
# BEGIN: Test case for ansible-galaxy
#

# Need a relative custom roles path for testing various scenarios of -p
galaxy_relative_rolespath="./my/custom/roles/path"

# Use geerlingguy's nginx galaxy role as the test dummy (it was the first
# one that came to mind, this could be something else if someone prefers)
galaxy_test_role="geerlingguy.nginx"
galaxy_test_role_github="https://github.com/geerlingguy/ansible-role-nginx.git"

# Galaxy install test case
#
# Ensure that if a role_path is passed, it is in fact used
ag_testdir=$(mktemp -d)
pushd "${ag_testdir}"
    mkdir -p "${galaxy_relative_rolespath}"

    ansible-galaxy install "${galaxy_test_role}" -p "${galaxy_relative_rolespath}"

    # Test that the role was installed to the expected directory
    [[ -d "${galaxy_relative_rolespath}/${galaxy_test_role}" ]]
popd # ${ag_testdir}
rm -fr "${ag_testdir}"

# Galaxy install test case
#
# Ensure that if both a role_file and role_path is provided, they are both
# honored
#
# Protect against regression (GitHub Issue #35217)
#   https://github.com/ansible/ansible/issues/35217

ag_testdir=$(mktemp -d)
pushd "${ag_testdir}"

    git clone "${galaxy_test_role_github}" "${galaxy_test_role}"
    ansible-galaxy init roles-path-bug
    pushd roles-path-bug
        cat <<EOF > ansible.cfg
[defaults]
roles_path = ../:../../:../roles:roles/
EOF
        cat <<EOF > requirements.yml
---
- src: ${galaxy_test_role_github}
  name: ${galaxy_test_role}
EOF

        ansible-galaxy install -r requirements.yml -p roles/
    popd # roles-path-bug

    # Test that the role was installed to the expected directory
    [[ -d "${ag_testdir}/roles-path-bug/roles/${galaxy_test_role}" ]]

popd # ${ag_testdir}
rm -fr "${ag_testdir}"


#
# END: Test case for ansible-galaxy
################################################################################
