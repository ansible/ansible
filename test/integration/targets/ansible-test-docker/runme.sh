#!/usr/bin/env bash

source ../collection/setup.sh

set -x

# common args for all tests
# because we are running in shippable/generic/ we are already in the default docker container
common=(--python "${ANSIBLE_TEST_PYTHON_VERSION}" --venv --venv-system-site-packages --color --truncate 0 "${@}")

# tests
ansible-test sanity "${common[@]}"
ansible-test units "${common[@]}"
ansible-test integration "${common[@]}"
