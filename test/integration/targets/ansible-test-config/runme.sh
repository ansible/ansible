#!/usr/bin/env bash
# Make sure that ansible-test is able to parse collection config when using a venv.

set -eu

source ../collection/setup.sh

set -x

# On systems with a Python version below the minimum controller Python version, such as the default container, this test
# will verify that the content config is working properly after delegation. Otherwise it will only verify that no errors
# occur while trying to access content config (such as missing requirements).

ansible-test sanity --test import --color --venv -v
ansible-test units --color --venv -v
