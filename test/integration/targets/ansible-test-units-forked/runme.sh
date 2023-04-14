#!/usr/bin/env bash

source ../collection/setup.sh

set -x

options=$("${TEST_DIR}"/../ansible-test/venv-pythons.py --only-versions)
IFS=', ' read -r -a pythons <<< "${options}"

for python in "${pythons[@]}"; do
  echo "*** Checking Python ${python} ***"

  if ansible-test units --truncate 0 --target-python "venv/${python}" "${@}" > output.log 2>&1 ; then
    cat output.log
    echo "Unit tests on Python ${python} did not fail as expected. See output above."
    exit 1
  fi

  cat output.log
  echo "Unit tests on Python ${python} failed as expected. See output above. Checking for expected output ..."

  # Verify that the appropriate tests pased, failed or xfailed.
  grep 'PASSED tests/unit/plugins/modules/test_ansible_forked.py::test_passed' output.log
  grep 'PASSED tests/unit/plugins/modules/test_ansible_forked.py::test_warning' output.log
  grep 'XFAIL tests/unit/plugins/modules/test_ansible_forked.py::test_kill_xfail' output.log
  grep 'FAILED tests/unit/plugins/modules/test_ansible_forked.py::test_kill' output.log
  grep 'FAILED tests/unit/plugins/modules/test_ansible_forked.py::test_exception' output.log
  grep 'XFAIL tests/unit/plugins/modules/test_ansible_forked.py::test_exception_xfail' output.log

  # Verify that warnings are properly surfaced.
  grep 'UserWarning: This verifies that warnings generated at test time are reported.' output.log
  grep 'UserWarning: This verifies that warnings generated during test collection are reported.' output.log

  # Verify there are no unexpected warnings.
  grep 'Warning' output.log | grep -v 'UserWarning: This verifies that warnings generated ' && exit 1

  # Verify that details from failed tests are properly surfaced.
  grep "^Test CRASHED with exit code -9.$" output.log
  grep "^This stdout message should be reported since we're throwing an exception.$" output.log
  grep "^This stderr message should be reported since we're throwing an exception.$" output.log
  grep '^> *raise Exception("This error is expected and should be visible.")$' output.log
  grep "^E *Exception: This error is expected and should be visible.$" output.log

  echo "*** Done Checking Python ${python} ***"
done
