#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

"${TEST_DIR}/collection-tests/update-ignore.py"

ansible-test sanity --color --truncate 0 "${@}"
