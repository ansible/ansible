#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook setup.yml "$@"

trap 'ansible-playbook cleanup.yml' EXIT

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

    printf "\n\n\n### Testing ansible-galaxy: %s\n" "${@}"
}

# Galaxy install test case
#
# Install local git repo
f_ansible_galaxy_status "install of local git repo"
galaxy_testdir=$(mktemp -d)
pushd "${galaxy_testdir}"

    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}" "$@"

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

    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}" -p "${galaxy_relative_rolespath}" "$@"

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
    ansible-galaxy init roles-path-bug "$@"
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

        ansible-galaxy install -r requirements.yml -p roles/ "$@"
    popd # roles-path-bug

    # Test that the role was installed to the expected directory
    [[ -d "${galaxy_testdir}/roles-path-bug/roles/${galaxy_local_test_role}" ]]

popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"

#################################
# ansible-galaxy collection tests
#################################

f_ansible_galaxy_status \
    "collection init tests to make sure the relative dir logic works"
galaxy_testdir=$(mktemp -d)
pushd "${galaxy_testdir}"

    ansible-galaxy collection init ansible_test.my_collection "$@"

    # Test that the collection skeleton was created in the expected directory
    for galaxy_collection_dir in "docs" "plugins" "roles"
    do
        [[ -d "${galaxy_testdir}/ansible_test/my_collection/${galaxy_collection_dir}" ]]
    done

popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"

f_ansible_galaxy_status \
    "collection init tests to make sure the --init-path logic works"
galaxy_testdir=$(mktemp -d)
pushd "${galaxy_testdir}"

    ansible-galaxy collection init ansible_test.my_collection --init-path "${galaxy_testdir}/test" "$@"

    # Test that the collection skeleton was created in the expected directory
    for galaxy_collection_dir in "docs" "plugins" "roles"
    do
        [[ -d "${galaxy_testdir}/test/ansible_test/my_collection/${galaxy_collection_dir}" ]]
    done

popd # ${galaxy_testdir}

f_ansible_galaxy_status \
    "collection build test creating artifact in current directory"

pushd "${galaxy_testdir}/test/ansible_test/my_collection"

    ansible-galaxy collection build "$@"

    [[ -f "${galaxy_testdir}/test/ansible_test/my_collection/ansible_test-my_collection-1.0.0.tar.gz" ]]

popd # ${galaxy_testdir}/ansible_test/my_collection

f_ansible_galaxy_status \
    "collection build test to make sure we can specify a relative path"

pushd "${galaxy_testdir}"

    ansible-galaxy collection build "test/ansible_test/my_collection" "$@"

    [[ -f "${galaxy_testdir}/ansible_test-my_collection-1.0.0.tar.gz" ]]

    # Make sure --force works
    ansible-galaxy collection build "test/ansible_test/my_collection" --force "$@"

    [[ -f "${galaxy_testdir}/ansible_test-my_collection-1.0.0.tar.gz" ]]

f_ansible_galaxy_status \
    "collection install from local tarball test"

    ansible-galaxy collection install "ansible_test-my_collection-1.0.0.tar.gz" -p ./install | tee out.txt

    [[ -f "${galaxy_testdir}/install/ansible_collections/ansible_test/my_collection/MANIFEST.json" ]]
    grep "Installing 'ansible_test.my_collection:1.0.0' to .*" out.txt


f_ansible_galaxy_status \
    "collection install with existing collection and without --force"

    ansible-galaxy collection install "ansible_test-my_collection-1.0.0.tar.gz" -p ./install | tee out.txt

    [[ -f "${galaxy_testdir}/install/ansible_collections/ansible_test/my_collection/MANIFEST.json" ]]
    grep "Skipping 'ansible_test.my_collection' as it is already installed" out.txt

f_ansible_galaxy_status \
    "collection install with existing collection and with --force"

    ansible-galaxy collection install "ansible_test-my_collection-1.0.0.tar.gz" -p ./install --force | tee out.txt

    [[ -f "${galaxy_testdir}/install/ansible_collections/ansible_test/my_collection/MANIFEST.json" ]]
    grep "Installing 'ansible_test.my_collection:1.0.0' to .*" out.txt

popd # ${galaxy_testdir}

rm -fr "${galaxy_testdir}"

rm -fr "${galaxy_local_test_role_dir}"
