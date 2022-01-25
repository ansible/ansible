#!/usr/bin/env bash

set -eux -o pipefail

cd "${WORK_DIR}"

if ansible-test --help 1>stdout 2>stderr; then
  echo "ansible-test did not fail"
  exit 1
fi

grep '^Current working directory: ' stderr

if grep raise stderr; then
  echo "ansible-test failed with a traceback instead of an error message"
  exit 2
fi
