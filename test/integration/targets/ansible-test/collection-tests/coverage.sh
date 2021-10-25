#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

"${TEST_DIR}/collection-tests/update-ignore.py"

# common args for all tests
common=(--venv --color --truncate 0 "${@}")

# run a lightweight test that generates code coverge output
ansible-test sanity --test import "${common[@]}" --coverage

# report on code coverage in all supported formats
ansible-test coverage report "${common[@]}"
ansible-test coverage html "${common[@]}"
ansible-test coverage xml "${common[@]}"
