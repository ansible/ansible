#!/usr/bin/env bash

set -ux

# ensure fail/assert work locally and can stop execution with non-zero exit code
PB_OUT=$(ansible-playbook -i inventory.local test_test_infra.yml)
APB_RC=$?
echo "$PB_OUT"
echo "rc was $APB_RC (must be non-zero)"
[ ${APB_RC} -ne 0 ]
echo "ensure playbook output shows assert/fail works (True)"
echo "$PB_OUT" | grep -F "fail works (True)" || exit 1
echo "$PB_OUT" | grep -F "assert works (True)" || exit 1

# ensure we work using all specified test args, overridden inventory, etc
PB_OUT=$(ansible-playbook -i ../../inventory test_test_infra.yml "$@")
APB_RC=$?
echo "$PB_OUT"
echo "rc was $APB_RC (must be non-zero)"
[ ${APB_RC} -ne 0 ]
echo "ensure playbook output shows assert/fail works (True)"
echo "$PB_OUT" | grep -F "fail works (True)" || exit 1
echo "$PB_OUT" | grep -F "assert works (True)" || exit 1

# ensure test-module script works well
PING_MODULE_PATH="$(pwd)/../../../../lib/ansible/modules/system/ping.py"
../../../../hacking/test-module -m "$PING_MODULE_PATH" -I ansible_python_interpreter="$(which python)"
