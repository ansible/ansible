#!/usr/bin/env bash

set -eu

NEEDS_SCRIPT=0

echo "checking for presence of script..."

command -v script || NEEDS_SCRIPT=1

if [ $NEEDS_SCRIPT == 1 ]; then
  echo "script missing, trying to install..."
  ansible-playbook test_setup.yml
fi

echo "testing for stdio deadlock on forked workers (10s timeout)..."

# Enable a callback that trips deadlocks on forked-child stdout, time out after 10s; uses `script` to force running
# in a pty, since that tends to be much slower than raw file I/O and thus more likely to trigger the deadlock.
# Redirect stdout to /dev/null since it's full of non-printable garbage we don't want to display unless it failed
ANSIBLE_CALLBACKS_ENABLED=spewstdio SPEWSTDIO_ENABLED=1 script -O stdout.txt -e -c 'timeout 10s ansible-playbook -i hosts -f 5 test.yml' > /dev/null && RC=$? || RC=$?

# FIXME apk add util-linux-misc on Alpine and remove afterward?

if [ $RC != 0 ]; then
  echo "failed; likely stdout deadlock. dumping raw output (may be very large)"
  cat stdout.txt
  exit 1
fi

grep -q -e "spewstdio STARTING NONPRINTING SPEW ON BACKGROUND THREAD" stdout.txt || (echo "spewstdio callback was not enabled"; exit 1)

if [ $NEEDS_SCRIPT == 1 ]; then
 echo "cleaning up script install"
 ansible-playbook test_teardown.yml
fi

echo "PASS"
