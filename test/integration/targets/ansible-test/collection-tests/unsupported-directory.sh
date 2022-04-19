#!/usr/bin/env bash

set -eux -o pipefail

cd "${WORK_DIR}"

# some options should succeed even in an unsupported directory
ansible-test --help
ansible-test --version

# the --help option should show the current working directory when it is unsupported
ansible-test --help 2>&1 | grep '^Current working directory: '

if ansible-test sanity 1>stdout 2>stderr; then
  echo "ansible-test did not fail"
  exit 1
fi

grep '^Current working directory: ' stderr

if grep raise stderr; then
  echo "ansible-test failed with a traceback instead of an error message"
  exit 2
fi
