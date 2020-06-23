#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/col"

# rename the sanity ignore file to match the current ansible version and update import ignores with the python version
ansible_version="$(python -c 'import ansible.release; print(".".join(ansible.release.__version__.split(".")[:2]))')"
sed "s/ import$/ import-${ANSIBLE_TEST_PYTHON_VERSION}/;" < "tests/sanity/ignore.txt" > "tests/sanity/ignore-${ansible_version}.txt"

# common args for all tests
# each test will be run in a separate venv to verify that requirements have been properly specified
common=(--venv --python "${ANSIBLE_TEST_PYTHON_VERSION}" --color --truncate 0 "${@}")

# sanity tests

tests=()

set +x

while IFS='' read -r line; do
  tests+=("$line");
done < <(
  ansible-test sanity --list-tests
)

set -x

for test in "${tests[@]}"; do
  rm -rf "tests/output"
  ansible-test sanity "${common[@]}" --test "${test}"
done

# unit tests

rm -rf "tests/output"
ansible-test units "${common[@]}"

# integration tests

rm -rf "tests/output"
ansible-test integration "${common[@]}"
