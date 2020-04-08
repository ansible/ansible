#!/usr/bin/env bash

set -eu -o pipefail

# tests must be executed outside of the ansible source tree
# otherwise ansible-test will test the ansible source instead of the test collection
# the temporary directory provided by ansible-test resides within the ansible source tree
tmp_dir=$(mktemp -d)

trap 'rm -rf "${tmp_dir}"' EXIT

export TEST_DIR
export WORK_DIR

TEST_DIR="$PWD"

for test in collection-tests/*.sh; do
  WORK_DIR="${tmp_dir}/$(basename "${test}" ".sh")"
  mkdir "${WORK_DIR}"
  echo "**********************************************************************"
  echo "TEST: ${test}: STARTING"
  "${test}" "${@}" || (echo "TEST: ${test}: FAILED" && exit 1)
  echo "TEST: ${test}: PASSED"
done
