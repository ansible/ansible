#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook setup.yml

# Need a relative custom roles path for testing various scenarios of -p
galaxy_relative_rolespath="my/custom/roles/path"

# Prep the local git repo with a role and make a tar archive so we can test
# different things
galaxy_local_test_role="test-role"
galaxy_local_test_role_dir=$(mktemp -d)
galaxy_local_test_role_git_repo="${galaxy_local_test_role_dir}/${galaxy_local_test_role}"
galaxy_local_test_role_tar="${galaxy_local_test_role_dir}/${galaxy_local_test_role}.tar"
pushd "${galaxy_local_test_role_dir}"
    ansible-galaxy init "${galaxy_local_test_role}"
    pushd "${galaxy_local_test_role}"
        git init .

        # Prep git, becuase it doesn't work inside a docker container without it
        git config user.email "tester@ansible.com"
        git config user.name "Ansible Tester"

        git add .
        git commit -m "local testing ansible galaxy role"
        git archive \
            --format=tar \
            --prefix="${galaxy_local_test_role}/" \
            master > "${galaxy_local_test_role_tar}"
    popd # "${galaxy_local_test_role}"
popd # "${galaxy_local_test_role_dir}"

# Status message function (f_ to designate that it's a function)
f_ansible_galaxy_status()
{

    printf "### Testing ansible-galaxy: %s\n" "${@}"
}

# Galaxy install test case
#
# Install local git repo
f_ansible_galaxy_status "install of local git repo"
galaxy_testdir=$(mktemp -d)
pushd "${galaxy_testdir}"

    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}"

    # Test that the role was installed to the expected directory
    [[ -d "${HOME}/.ansible/roles/${galaxy_local_test_role}" ]]
popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"

# Galaxy install test case
#
# Install local git repo and ensure that if a role_path is passed, it is in fact used
f_ansible_galaxy_status "install of local git repo with -p \$role_path"
galaxy_testdir=$(mktemp -d)
pushd "${galaxy_testdir}"
    mkdir -p "${galaxy_relative_rolespath}"

    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}" -p "${galaxy_relative_rolespath}"

    # Test that the role was installed to the expected directory
    [[ -d "${galaxy_relative_rolespath}/${galaxy_local_test_role}" ]]
popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"

# Galaxy install test case
#
# Ensure that if both a role_file and role_path is provided, they are both
# honored
#
# Protect against regression (GitHub Issue #35217)
#   https://github.com/ansible/ansible/issues/35217

f_ansible_galaxy_status \
    "install of local git repo and local tarball with -p \$role_path and -r \$role_file" \
    "Protect against regression (Issue #35217)"
galaxy_testdir=$(mktemp -d)
pushd "${galaxy_testdir}"

    git clone "${galaxy_local_test_role_git_repo}" "${galaxy_local_test_role}"
    ansible-galaxy init roles-path-bug
    pushd roles-path-bug
        cat <<EOF > ansible.cfg
[defaults]
roles_path = ../:../../:../roles:roles/
EOF
        cat <<EOF > requirements.yml
---
- src: ${galaxy_local_test_role_tar}
  name: ${galaxy_local_test_role}
EOF

        ansible-galaxy install -r requirements.yml -p roles/
    popd # roles-path-bug

    # Test that the role was installed to the expected directory
    [[ -d "${galaxy_testdir}/roles-path-bug/roles/${galaxy_local_test_role}" ]]

popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"


rm -fr "${galaxy_local_test_role_dir}"
