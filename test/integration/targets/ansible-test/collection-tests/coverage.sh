#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

# rename the sanity ignore file to match the current ansible version and update import ignores with the python version
ansible_version="$(python -c 'import ansible.release; print(".".join(ansible.release.__version__.split(".")[:2]))')"
if [ "${ANSIBLE_TEST_PYTHON_VERSION}" == "2.6" ]; then
    # Non-module/module_utils plugins are not checked on this remote-only Python versions
    sed "s/ import$/ import-${ANSIBLE_TEST_PYTHON_VERSION}/;" < "tests/sanity/ignore.txt" | grep -v 'plugins/[^m].* import' > "tests/sanity/ignore-${ansible_version}.txt"
else
    sed "s/ import$/ import-${ANSIBLE_TEST_PYTHON_VERSION}/;" < "tests/sanity/ignore.txt" > "tests/sanity/ignore-${ansible_version}.txt"
fi
cat "tests/sanity/ignore-${ansible_version}.txt"

# common args for all tests
common=(--venv --color --truncate 0 "${@}")
test_common=("${common[@]}" --python "${ANSIBLE_TEST_PYTHON_VERSION}")

# run a lightweight test that generates code coverge output
ansible-test sanity --test import "${test_common[@]}" --coverage

# report on code coverage in all supported formats
ansible-test coverage report "${common[@]}"
ansible-test coverage html "${common[@]}"
ansible-test coverage xml "${common[@]}"
