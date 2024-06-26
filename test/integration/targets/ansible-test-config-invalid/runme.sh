#!/usr/bin/env bash
# Make sure that ansible-test continues to work when content config is invalid.

set -eu

source ../collection/setup.sh

set -x

ansible-test sanity --test import --python "${ANSIBLE_TEST_PYTHON_VERSION}" --color --venv -v
ansible-test units  --python "${ANSIBLE_TEST_PYTHON_VERSION}" --color --venv -v
ansible-test integration --color --venv -v
