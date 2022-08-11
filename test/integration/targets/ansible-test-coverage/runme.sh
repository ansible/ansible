#!/usr/bin/env bash

source ../collection/setup.sh

set -x

# common args for all tests
common=(--venv --color --truncate 0 "${@}")

# run a lightweight test that generates code coverge output
ansible-test sanity --test import "${common[@]}" --coverage

# report on code coverage in all supported formats
ansible-test coverage report "${common[@]}"
ansible-test coverage html "${common[@]}"
ansible-test coverage xml "${common[@]}"
