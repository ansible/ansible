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

set -e

PING_MODULE_PATH="../../../../lib/ansible/modules/system/ping.py"

# ensure test-module.py script works without passing Python interpreter path
../../../../hacking/test-module.py -m "$PING_MODULE_PATH"

# ensure test-module.py script works well
../../../../hacking/test-module.py -m "$PING_MODULE_PATH" -I ansible_python_interpreter="$(which python)"

# ensure module.ansible_version is defined when using test-module.py
../../../../hacking/test-module.py -m library/test.py -I ansible_python_interpreter="$(which python)" <<< '{"ANSIBLE_MODULE_ARGS": {}}'

# ensure exercising module code locally works
python -m ansible.modules.files.file  <<< '{"ANSIBLE_MODULE_ARGS": {"path": "/path/to/file", "state": "absent"}}'
