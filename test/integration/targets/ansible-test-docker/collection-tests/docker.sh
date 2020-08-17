#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

# common args for all tests
# because we are running in shippable/generic/ we are already in the default docker container
common=(--python "${ANSIBLE_TEST_PYTHON_VERSION}" --color --truncate 0 "${@}")

# prime the venv to work around issue with PyYAML detection in ansible-test
ansible-test sanity "${common[@]}" --test ignores

# tests
ansible-test sanity "${common[@]}"
ansible-test units "${common[@]}"
ansible-test integration "${common[@]}"
