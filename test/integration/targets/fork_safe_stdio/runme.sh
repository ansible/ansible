#!/usr/bin/env bash

set -eu

echo "testing for stdio deadlock on forked workers (10s timeout)..."

# Enable a callback that trips deadlocks on forked-child stdout, time out after 10s; forces running
# in a pty, since that tends to be much slower than raw file I/O and thus more likely to trigger the deadlock.
# Redirect stdout to /dev/null since it's full of non-printable garbage we don't want to display unless it failed
ANSIBLE_CALLBACKS_ENABLED=spewstdio SPEWSTDIO_ENABLED=1 python run-with-pty.py ../test_utils/scripts/timeout.py -- 10 ansible-playbook -i hosts -f 5 test.yml > stdout.txt && RC=$? || RC=$?

if [ "${RC}" != 0 ]; then
  echo "failed; likely stdout deadlock. dumping raw output (may be very large)"
  cat stdout.txt
  exit 1
fi

grep -q -e "spewstdio STARTING NONPRINTING SPEW ON BACKGROUND THREAD" stdout.txt || (echo "spewstdio callback was not enabled"; exit 1)

echo "PASS"
