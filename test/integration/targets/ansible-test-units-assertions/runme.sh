#!/usr/bin/env bash

source ../collection/setup.sh

set -x

options=$("${TEST_DIR}"/../ansible-test/venv-pythons.py --only-versions)
IFS=', ' read -r -a pythons <<< "${options}"

for python in "${pythons[@]}"; do
  if ansible-test units --truncate 0 --python "${python}" --requirements "${@}" 2>&1 | tee pytest.log; then
    echo "Test did not fail as expected."
    exit 1
  fi

  if [ "${python}" = "2.7" ]; then
    grep "^E  *AssertionError$" pytest.log
  else

    grep "^E  *AssertionError: assert {'yes': True} == {'no': False}$" pytest.log
  fi
done
