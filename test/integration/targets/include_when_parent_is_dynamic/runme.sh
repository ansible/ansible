#!/usr/bin/env bash

set -eu

ansible-playbook playbook.yml "$@" > output.log 2>&1 || true

if grep "task should always execute" output.log >/dev/null; then
  echo "Test passed (playbook failed with expected output, output not shown)."
  exit 0
fi

cat output.log
exit 1
