#!/usr/bin/env bash

set -eu

source ../collection/setup.sh

set -x

ansible-test sanity --test use-compat-six --color --lint --failure-ok "${@}" > actual.txt

diff -u "${TEST_DIR}/expected.txt" actual.txt
diff -u do-not-check-me.py plugins/modules/check-me.py
