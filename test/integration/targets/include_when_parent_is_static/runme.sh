#!/usr/bin/env bash

set -eux

ansible-playbook playbook.yml "$@" > output.log 2>&1 || true

if grep "intentional syntax error" output.log >/dev/null; then
  echo "Test passed (playbook failed with expected output, output not shown)."
  exit 0
fi

cat output.log
exit 1
