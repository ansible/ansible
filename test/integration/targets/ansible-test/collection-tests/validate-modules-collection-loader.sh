#!/usr/bin/env bash

set -eux -o pipefail

cp -a "${TEST_DIR}/ansible_collections" "${WORK_DIR}"
cd "${WORK_DIR}/ansible_collections/ns/ps_only"

# Use a PowerShell-only collection to verify that validate-modules does not load the collection loader multiple times.
ansible-test sanity --test validate-modules --color --truncate 0 "${@}"
