#!/usr/bin/env bash

source ../collection/setup.sh

set -x

# common args for all tests
common=(--venv --color --truncate 0 "${@}")

# run a lightweight test that generates code coverage output
ansible-test sanity --test import "${common[@]}" --coverage --python "${ANSIBLE_TEST_PYTHON_VERSION}"

# run an integration test that generates code coverage for a Python file within the integration test
ansible-test integration "${common[@]}" --coverage

# run a unit test that generates code coverage using a venv
ansible-test units "${common[@]}" --coverage --python "${ANSIBLE_TEST_PYTHON_VERSION}" --venv

# report on code coverage in all supported formats
ansible-test coverage report "${common[@]}" | tee coverage.report
ansible-test coverage html "${common[@]}"
ansible-test coverage xml "${common[@]}"

# ensure import test coverage was collected
grep '^plugins/module_utils/test_util.py .* 100%$' coverage.report

# ensure integration test coverage was collected
grep '^tests/integration/targets/hello/world.py .* 100%$' coverage.report

# ensure unit test coverage was collected
grep '^tests/unit/test_something.py .* 100%$' coverage.report

# ensure tests/output/ (from --venv) does not appear in the coverage report (except in the report filename)
if grep "^tests/output/" coverage.report; then
  echo "unexpected coverage output: tests/output/"
  exit 1
fi
