#!/usr/bin/env bash

source ../collection/setup.sh

set -x

ansible-test integration without --venv --color --truncate 0 "${@}"

export MYVAR1='one'
export MYVAR2='two'
export ANSIBLE_TEST_PASS_ENV='ANSIBLE_TEST_PASS_ENV MYVAR1 MYVAR2 MYVAR3'

ansible-test integration with --venv --color --truncate 0 "${@}"
