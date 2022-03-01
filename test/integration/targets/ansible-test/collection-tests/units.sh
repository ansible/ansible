#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

options=$("${TEST_DIR}"/collection-tests/venv-pythons.py)
IFS=', ' read -r -a pythons <<< "${options}"

ansible-test units --color --truncate 0 "${pythons[@]}" "${@}"
