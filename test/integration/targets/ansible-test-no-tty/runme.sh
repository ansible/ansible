#!/usr/bin/env bash
# Verify that ansible-test runs integration tests without a TTY.

source ../collection/setup.sh

set -x

if ./run-with-pty.py tests/integration/targets/no-tty/assert-no-tty.py > /dev/null; then
  echo "PTY assertion did not fail. Either PTY creation failed or PTY detection is broken."
  exit 1
fi

./run-with-pty.py ansible-test integration --color "${@}"
