#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/ps_only"

if ! command -V pwsh; then
  echo "skipping test since pwsh is not available"
  exit 0
fi

# Use a PowerShell-only collection to verify that validate-modules does not load the collection loader multiple times.
ansible-test sanity --test validate-modules --color --truncate 0 "${@}"
