#!/usr/bin/env bash

source ../collection/setup.sh

set -x

options=$("${TEST_DIR}"/../ansible-test/venv-pythons.py)
IFS=', ' read -r -a pythons <<< "${options}"

ansible-test units --color --truncate 0 "${pythons[@]}" "${@}"
