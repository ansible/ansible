#!/usr/bin/env bash

set -eux -o pipefail

# tests must be executed outside of the ansible source tree
# otherwise ansible-test will test the ansible source instead of the test collection
# the temporary directory provided by ansible-test resides within the ansible source tree
tmp_dir=$(mktemp -d)

trap 'rm -rf "${tmp_dir}"' EXIT

cp -a ansible_collections "${tmp_dir}"
cd "${tmp_dir}/ansible_collections/ns/col"

# common args for all tests
common=(--venv --python "${ANSIBLE_TEST_PYTHON_VERSION}" --color --truncate 0 "${@}")

# prime the venv to work around issue with PyYAML detection in ansible-test
ansible-test sanity "${common[@]}" --test ignores

# tests
ansible-test sanity "${common[@]}"
ansible-test units "${common[@]}"
ansible-test integration "${common[@]}"
