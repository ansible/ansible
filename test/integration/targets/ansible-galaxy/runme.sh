#!/usr/bin/env bash

set -eux -o pipefail

galaxy_testdir="${OUTPUT_DIR}/galaxy-test-dir"
role_testdir="${OUTPUT_DIR}/role-test-dir"
# Prep the local git repos with role and make a tar archive so we can test
# different things
galaxy_local_test_role="test-role"
galaxy_local_test_role_dir="${OUTPUT_DIR}/galaxy-role-test-root"
galaxy_local_test_role_git_repo="${galaxy_local_test_role_dir}/${galaxy_local_test_role}"
galaxy_local_test_role_tar="${galaxy_local_test_role_dir}/${galaxy_local_test_role}.tar"
galaxy_webserver_root="${OUTPUT_DIR}/ansible-galaxy-webserver"

mkdir -p "${galaxy_local_test_role_dir}"
mkdir -p "${role_testdir}"
mkdir -p "${galaxy_webserver_root}"

ansible-playbook setup.yml "$@"

trap 'ansible-playbook ${ANSIBLE_PLAYBOOK_DIR}/cleanup.yml' EXIT

# Very simple version test
ansible-galaxy --version

# Need a relative custom roles path for testing various scenarios of -p
galaxy_relative_rolespath="my/custom/roles/path"

# Status message function (f_ to designate that it's a function)
f_ansible_galaxy_status()
{
    printf "\n\n\n### Testing ansible-galaxy: %s\n" "${@}"
}

# Use to initialize a repository. Must call the post function too.
f_ansible_galaxy_create_role_repo_pre()
{
    repo_name=$1
    repo_dir=$2

    pushd "${repo_dir}"
        ansible-galaxy init "${repo_name}"
        pushd "${repo_name}"
            git init .

            # Prep git, because it doesn't work inside a docker container without it
            git config user.email "tester@ansible.com"
            git config user.name "Ansible Tester"

    # f_ansible_galaxy_create_role_repo_post
}

# Call after f_ansible_galaxy_create_repo_pre.
f_ansible_galaxy_create_role_repo_post()
{
    repo_name=$1
    repo_tar=$2

    # f_ansible_galaxy_create_role_repo_pre

            git add .
            git commit -m "local testing ansible galaxy role"

            # NOTE: `HEAD` is used because the newer Git versions create
            # NOTE: `main` by default and the older ones differ. We
            # NOTE: want to avoid hardcoding them.
            git archive \
                --format=tar \
                --prefix="${repo_name}/" \
                HEAD > "${repo_tar}"
            # Configure basic (insecure) HTTPS-accessible repository
            galaxy_local_test_role_http_repo="${galaxy_webserver_root}/${galaxy_local_test_role}.git"
            if [[ ! -d "${galaxy_local_test_role_http_repo}" ]]; then
                git clone --bare "${galaxy_local_test_role_git_repo}" "${galaxy_local_test_role_http_repo}"
                pushd "${galaxy_local_test_role_http_repo}"
                    touch "git-daemon-export-ok"
                    git --bare update-server-info
                    mv "hooks/post-update.sample" "hooks/post-update"
                popd # ${galaxy_local_test_role_http_repo}
            fi
        popd # "${repo_name}"
    popd # "${repo_dir}"
}

f_ansible_galaxy_create_role_repo_pre "${galaxy_local_test_role}" "${galaxy_local_test_role_dir}"
f_ansible_galaxy_create_role_repo_post "${galaxy_local_test_role}" "${galaxy_local_test_role_tar}"

galaxy_local_parent_role="parent-role"
galaxy_local_parent_role_dir="${OUTPUT_DIR}/parent-role"
mkdir -p "${galaxy_local_parent_role_dir}"
galaxy_local_parent_role_git_repo="${galaxy_local_parent_role_dir}/${galaxy_local_parent_role}"
galaxy_local_parent_role_tar="${galaxy_local_parent_role_dir}/${galaxy_local_parent_role}.tar"

# Create parent-role repository
f_ansible_galaxy_create_role_repo_pre "${galaxy_local_parent_role}" "${galaxy_local_parent_role_dir}"

    cat <<EOF > meta/requirements.yml
- src: git+file:///${galaxy_local_test_role_git_repo}
EOF
f_ansible_galaxy_create_role_repo_post "${galaxy_local_parent_role}" "${galaxy_local_parent_role_tar}"

# Galaxy install test case
#
# Install local git repo
f_ansible_galaxy_status "install of local git repo"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"

    # minimum verbosity is hardcoded to include calls to Galaxy
    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}" "$@" -vvvv 2>&1 | tee out.txt

    # Test no initial call is made to Galaxy
    grep out.txt -e "https://galaxy.ansible.com" && cat out.txt && exit 1

    # Test that the role was installed to the expected directory
    [[ -d "${HOME}/.ansible/roles/${galaxy_local_test_role}" ]]
popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"
rm -fr "${HOME}/.ansible/roles/${galaxy_local_test_role}"

# Galaxy install test case
#
# Install local git repo and ensure that if a role_path is passed, it is in fact used
f_ansible_galaxy_status "install of local git repo with -p \$role_path"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"
    mkdir -p "${galaxy_relative_rolespath}"

    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}" -p "${galaxy_relative_rolespath}" "$@"

    # Test that the role was installed to the expected directory
    [[ -d "${galaxy_relative_rolespath}/${galaxy_local_test_role}" ]]
popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"

# Galaxy install test case - skipping cert verification
#
# Install from remote git repo and ensure that cert validation is skipped
#
# Protect against regression (GitHub Issue #41077)
#   https://github.com/ansible/ansible/issues/41077
f_ansible_galaxy_status "install of role from untrusted repository"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"
    mkdir -p "${galaxy_relative_rolespath}"

    # Without --ignore-certs, installing a role from an untrusted repository should fail
    set +e
    ansible-galaxy install --verbose git+https://localhost:4443/"${galaxy_local_test_role}.git" -p "${galaxy_relative_rolespath}" "$@" 2>&1 | tee out.txt
    ansible_exit_code="$?"
    set -e
    cat out.txt

    if [[ "$ansible_exit_code" -ne 1 ]]; then echo "Exit code ($ansible_exit_code) is expected to be 1" && exit "$ansible_exit_code"; fi
    [[ $(grep -c 'ERROR' out.txt) -eq 1 ]]
    [[ ! -d "${galaxy_relative_rolespath}/${galaxy_local_test_role}" ]]

    ansible-galaxy install --verbose --ignore-certs git+https://localhost:4443/"${galaxy_local_test_role}.git" -p "${galaxy_relative_rolespath}" "$@"

    # Test that the role was installed to the expected directory
    [[ -d "${galaxy_relative_rolespath}/${galaxy_local_test_role}" ]]
popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"

# Galaxy install test case
#
# Install local git repo with a meta/requirements.yml
f_ansible_galaxy_status "install of local git repo with meta/requirements.yml"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"

    ansible-galaxy install git+file:///"${galaxy_local_parent_role_git_repo}" "$@"

    # Test that the role was installed to the expected directory
    [[ -d "${HOME}/.ansible/roles/${galaxy_local_parent_role}" ]]

    # Test that the dependency was also installed
    [[ -d "${HOME}/.ansible/roles/${galaxy_local_test_role}" ]]

popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"
rm -fr "${HOME}/.ansible/roles/${galaxy_local_parent_role}"
rm -fr "${HOME}/.ansible/roles/${galaxy_local_test_role}"

# Galaxy install test case
#
# Install local git repo with a meta/requirements.yml + --no-deps argument
f_ansible_galaxy_status "install of local git repo with meta/requirements.yml + --no-deps argument"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"

    ansible-galaxy install git+file:///"${galaxy_local_parent_role_git_repo}" --no-deps "$@"

    # Test that the role was installed to the expected directory
    [[ -d "${HOME}/.ansible/roles/${galaxy_local_parent_role}" ]]

    # Test that the dependency was not installed
    [[ ! -d "${HOME}/.ansible/roles/${galaxy_local_test_role}" ]]

popd # ${galaxy_testdir}
rm -fr "${galaxy_testdir}"
rm -fr "${HOME}/.ansible/roles/${galaxy_local_test_role}"

# Galaxy install test case (expected failure)
#
# Install role with a meta/requirements.yml that is not a list of roles
mkdir -p "${role_testdir}"
pushd "${role_testdir}"

    ansible-galaxy role init --init-path . unsupported_requirements_format
    cat <<EOF > ./unsupported_requirements_format/meta/requirements.yml
roles:
  - src: git+file:///${galaxy_local_test_role_git_repo}
EOF
    tar czvf unsupported_requirements_format.tar.gz unsupported_requirements_format

    set +e
    ansible-galaxy role install -p ./roles unsupported_requirements_format.tar.gz 2>&1 | tee out.txt
    rc="$?"
    set -e

    # Test that installing the role was an error
    [[ ! "$rc" == 0 ]]
    grep out.txt -qe 'Expected role dependencies to be a list.'

    # Test that the role was not installed to the expected directory
    [[ ! -d "${HOME}/.ansible/roles/unsupported_requirements_format" ]]

popd # ${role_testdir}
rm -rf "${role_testdir}"

# Galaxy install test case (expected failure)
#
# Install role with meta/main.yml dependencies that is not a list of roles
mkdir -p "${role_testdir}"
pushd "${role_testdir}"

    ansible-galaxy role init --init-path . unsupported_requirements_format
    cat <<EOF > ./unsupported_requirements_format/meta/main.yml
galaxy_info:
  author: Ansible
  description: test unknown dependency format (expected failure)
  company: your company (optional)
  license: license (GPL-2.0-or-later, MIT, etc)
  min_ansible_version: 2.1
  galaxy_tags: []
dependencies:
  roles:
    - src: git+file:///${galaxy_local_test_role_git_repo}
EOF
    tar czvf unsupported_requirements_format.tar.gz unsupported_requirements_format

    set +e
    ansible-galaxy role install -p ./roles unsupported_requirements_format.tar.gz 2>&1 | tee out.txt
    rc="$?"
    set -e

    # Test that installing the role was an error
    [[ ! "$rc" == 0 ]]
    grep out.txt -qe 'Expected role dependencies to be a list.'

    # Test that the role was not installed to the expected directory
    [[ ! -d "${HOME}/.ansible/roles/unsupported_requirements_format" ]]

popd # ${role_testdir}
rm -rf "${role_testdir}"

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
mkdir -p "${galaxy_testdir}"
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


# Galaxy role list tests
#
# Basic tests to ensure listing roles works

f_ansible_galaxy_status "role list"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"
    ansible-galaxy install git+file:///"${galaxy_local_test_role_git_repo}" "$@"

    ansible-galaxy role list | tee out.txt
    ansible-galaxy role list test-role | tee -a out.txt

    [[ $(grep -c '^- test-role' out.txt ) -eq 2 ]]
popd # ${galaxy_testdir}

# Galaxy role test case
#
# Test listing a specific role that is not in the first path in ANSIBLE_ROLES_PATH.
# https://github.com/ansible/ansible/issues/60167#issuecomment-585460706

f_ansible_galaxy_status \
    "list specific role not in the first path in ANSIBLE_ROLES_PATH"

mkdir -p "${role_testdir}"
pushd "${role_testdir}"

    mkdir testroles
    ansible-galaxy role init --init-path ./local-roles quark
    ANSIBLE_ROLES_PATH=./local-roles:${HOME}/.ansible/roles ansible-galaxy role list quark | tee out.txt

    [[ $(grep -c 'not found' out.txt) -eq 0 ]]

    ANSIBLE_ROLES_PATH=${HOME}/.ansible/roles:./local-roles ansible-galaxy role list quark | tee out.txt

    [[ $(grep -c 'not found' out.txt) -eq 0 ]]

popd # ${role_testdir}
rm -fr "${role_testdir}"


# Galaxy role info tests

# Get info about role that is not installed

f_ansible_galaxy_status "role info"
mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"
    ansible-galaxy role info samdoran.fish | tee out.txt

    [[ $(grep -c 'not found' out.txt ) -eq 0 ]]
    [[ $(grep -c 'Role:.*samdoran\.fish' out.txt ) -eq 1 ]]

popd # ${galaxy_testdir}

f_ansible_galaxy_status \
    "role info non-existent role"

mkdir -p "${role_testdir}"
pushd "${role_testdir}"

    ansible-galaxy role info notaroll | tee out.txt

    grep -- '- the role notaroll was not found' out.txt

f_ansible_galaxy_status \
    "role info description offline"

    mkdir testroles
    ansible-galaxy role init testdesc --init-path ./testroles

    # Only galaxy_info['description'] exists in file
    sed -i -e 's#[[:space:]]\{1,\}description:.*$#  description: Description in galaxy_info#' ./testroles/testdesc/meta/main.yml
    ansible-galaxy role info -p ./testroles --offline testdesc | tee out.txt
    grep 'description: Description in galaxy_info' out.txt

    # Both top level 'description' and galaxy_info['description'] exist in file
    # Use shell-fu instead of sed to prepend a line to a file because BSD
    # and macOS sed don't work the same as GNU sed.
    echo 'description: Top level' | \
        cat - ./testroles/testdesc/meta/main.yml > tmp.yml && \
        mv tmp.yml ./testroles/testdesc/meta/main.yml
    ansible-galaxy role info -p ./testroles --offline testdesc | tee out.txt
    grep 'description: Top level' out.txt

    # Only top level 'description' exists in file
    sed -i.bak '/^[[:space:]]\{1,\}description: Description in galaxy_info/d' ./testroles/testdesc/meta/main.yml
    ansible-galaxy role info -p ./testroles --offline testdesc | tee out.txt
    grep 'description: Top level' out.txt

    # test multiple role listing
    ansible-galaxy role init otherrole --init-path ./testroles
    ansible-galaxy role info -p ./testroles --offline testdesc otherrole | tee out.txt
    grep 'Role: testdesc' out.txt
    grep 'Role: otherrole' out.txt


popd # ${role_testdir}
rm -fr "${role_testdir}"

# Properly list roles when the role name is a subset of the path, or the role
# name is the same name as the parent directory of the role. Issue #67365
#
# ./parrot/parrot
# ./parrot/arr
# ./testing-roles/test

f_ansible_galaxy_status \
    "list roles where the role name is the same or a subset of the role path (#67365)"

mkdir -p "${role_testdir}"
pushd "${role_testdir}"

    mkdir parrot
    ansible-galaxy role init --init-path ./parrot parrot
    ansible-galaxy role init --init-path ./parrot parrot-ship
    ansible-galaxy role init --init-path ./parrot arr

    ansible-galaxy role list -p ./parrot | tee out.txt

    [[ $(grep -Ec '\- (parrot|arr)' out.txt) -eq 3 ]]
    ansible-galaxy role list test-role | tee -a out.txt

popd # ${role_testdir}
rm -rf "${role_testdir}"

f_ansible_galaxy_status \
    "Test role with non-ascii characters"

mkdir -p "${role_testdir}"
pushd "${role_testdir}"

    mkdir nonascii
    ansible-galaxy role init --init-path ./nonascii nonascii
    touch nonascii/ÅÑŚÌβŁÈ.txt
    tar czvf nonascii.tar.gz nonascii
    ansible-galaxy role install -p ./roles nonascii.tar.gz

popd # ${role_testdir}
rm -rf "${role_testdir}"

f_ansible_galaxy_status \
    "Test if git hidden directories are skipped while using role skeleton (#71977)"

role_testdir=$(mktemp -d)
pushd "${role_testdir}"

    ansible-galaxy role init sample-role-skeleton
    git init ./sample-role-skeleton
    ansible-galaxy role init --role-skeleton=sample-role-skeleton example

popd # ${role_testdir}
rm -rf "${role_testdir}"

#################################
# ansible-galaxy collection tests
#################################
# TODO: Move these to ansible-galaxy-collection

mkdir -p "${galaxy_testdir}"
pushd "${galaxy_testdir}"

## ansible-galaxy collection list tests

# Create more collections and put them in various places
f_ansible_galaxy_status \
    "setting up for collection list tests"

rm -rf ansible_test/* install/*

NAMES=(zoo museum airport)
for n in "${NAMES[@]}"; do
    ansible-galaxy collection init "ansible_test.$n"
    ansible-galaxy collection build "ansible_test/$n"
done

ansible-galaxy collection install ansible_test-zoo-1.0.0.tar.gz
ansible-galaxy collection install ansible_test-museum-1.0.0.tar.gz -p ./install
ansible-galaxy collection install ansible_test-airport-1.0.0.tar.gz -p ./local

# Change the collection version and install to another location
sed -i -e 's#^version:.*#version: 2.5.0#' ansible_test/zoo/galaxy.yml
ansible-galaxy collection build ansible_test/zoo
ansible-galaxy collection install ansible_test-zoo-2.5.0.tar.gz -p ./local

# Test listing a collection that contains a galaxy.yml
ansible-galaxy collection init "ansible_test.development"
mv ./ansible_test/development "${galaxy_testdir}/local/ansible_collections/ansible_test/"

export ANSIBLE_COLLECTIONS_PATH=~/.ansible/collections:${galaxy_testdir}/local

f_ansible_galaxy_status \
    "collection list all collections"

    ansible-galaxy collection list -p ./install | tee out.txt

    [[ $(grep -c ansible_test out.txt) -eq 5 ]]

f_ansible_galaxy_status \
    "collection list specific collection"

    ansible-galaxy collection list -p ./install ansible_test.airport | tee out.txt

    [[ $(grep -c 'ansible_test\.airport' out.txt) -eq 1 ]]

f_ansible_galaxy_status \
    "collection list specific collection which contains galaxy.yml"

    ansible-galaxy collection list -p ./install ansible_test.development 2>&1 | tee out.txt

    [[ $(grep -c 'ansible_test\.development' out.txt) -eq 1 ]]
    [[ $(grep -c 'WARNING' out.txt) -eq 0 ]]

f_ansible_galaxy_status \
    "collection list specific collection found in multiple places"

    ansible-galaxy collection list -p ./install ansible_test.zoo | tee out.txt

    [[ $(grep -c 'ansible_test\.zoo' out.txt) -eq 2 ]]

f_ansible_galaxy_status \
    "collection list all with duplicate paths"

    ansible-galaxy collection list -p ~/.ansible/collections | tee out.txt

    [[ $(grep -c '# /root/.ansible/collections/ansible_collections' out.txt) -eq 1 ]]

f_ansible_galaxy_status \
    "collection list invalid collection name"

    ansible-galaxy collection list -p ./install dirty.wraughten.name "$@" 2>&1 | tee out.txt || echo "expected failure"

    grep 'ERROR! Invalid collection name' out.txt

f_ansible_galaxy_status \
    "collection list path not found"

    ansible-galaxy collection list -p ./nope "$@" 2>&1 | tee out.txt || echo "expected failure"

    grep '\[WARNING\]: - the configured path' out.txt

f_ansible_galaxy_status \
    "collection list missing ansible_collections dir inside path"

    mkdir emptydir

    ansible-galaxy collection list -p ./emptydir "$@"

    rmdir emptydir

unset ANSIBLE_COLLECTIONS_PATH

f_ansible_galaxy_status \
    "collection list with collections installed from python package"

    mkdir -p test-site-packages
    ln -s "${galaxy_testdir}/local/ansible_collections" test-site-packages/ansible_collections
    ansible-galaxy collection list
    PYTHONPATH="./test-site-packages/:$PYTHONPATH" ansible-galaxy collection list | tee out.txt

    grep ".ansible/collections/ansible_collections" out.txt
    grep "test-site-packages/ansible_collections" out.txt

## end ansible-galaxy collection list


popd # ${galaxy_testdir}

rm -fr "${galaxy_testdir}"

rm -fr "${galaxy_local_test_role_dir}"
