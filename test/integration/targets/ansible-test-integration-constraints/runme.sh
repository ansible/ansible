#!/usr/bin/env bash

source ../collection/setup.sh

set -x

ansible-test integration --venv --color --truncate 0 "${@}"
