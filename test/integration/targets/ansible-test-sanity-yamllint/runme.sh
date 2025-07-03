#!/usr/bin/env bash

set -eu

source ../collection/setup.sh

set -x

ansible-test sanity --test yamllint --color --lint --failure-ok "${@}" > actual.txt

diff -u "${TEST_DIR}/expected.txt" actual.txt
