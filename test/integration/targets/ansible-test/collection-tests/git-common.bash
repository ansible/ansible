#!/usr/bin/env bash

set -eux -o pipefail

# make sure git is installed
git --version || ansible-playbook collection-tests/install-git.yml -i ../../inventory "$@"

# init sub project
mkdir "${WORK_DIR}/sub"
cd "${WORK_DIR}/sub"
touch "README.md"
git init
git config user.name 'Ansible Test'
git config user.email 'ansible-test@ansible.com'
git add "README.md"
git commit -m "Initial commit."

# init super project
rm -rf "${WORK_DIR}/super" # needed when re-creating in place
mkdir "${WORK_DIR}/super"
cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}/super"
cd "${GIT_TOP_LEVEL}"
git init

# add submodule
git submodule add "${WORK_DIR}/sub" "${SUBMODULE_DST}"

# prepare for tests
expected="${WORK_DIR}/expected.txt"
actual="${WORK_DIR}/actual.txt"
cd "${WORK_DIR}/super/ansible_collections/ns/col"
mkdir tests/.git
touch tests/.git/keep.txt  # make sure ansible-test correctly ignores version control within collection subdirectories
find . -type f ! -path '*/.git/*' ! -name .git | sed 's|^\./||' | sort >"${expected}"
set -x

# test at the collection base
ansible-test env --list-files | sort >"${actual}"
diff --unified "${expected}" "${actual}"

# test at the submodule base
(cd sub && ansible-test env --list-files | sort >"${actual}")
diff --unified "${expected}" "${actual}"
