#!/usr/bin/env bash

TEST_PATH="${PWD}/test-coverage.py"

source ../collection/setup.sh
cp "${INVENTORY_PATH}" tests/integration/inventory.winrm

set -x

# common args for all tests
common=(--venv --color --truncate 0 "${@}")

# run command that generates coverage data for Windows
ansible-test windows-integration win_collection "${common[@]}" --coverage

# report on code coverage in all supported formats
ansible-test coverage report "${common[@]}"

# test we covered the 2 files we expect to have been covered and their lines
python "${TEST_PATH}"
