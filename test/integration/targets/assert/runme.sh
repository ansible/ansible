#!/usr/bin/env bash

# This test compares "known good" output with various settings against output
# with the current code. It's brittle by nature, but this is probably the
# "best" approach possible.
#
# Notes:
# * options passed to this script (such as -v) are ignored, as they would change
#   the output and break the test
# * the number of asterisks after a "banner" differs is forced to 79 by
#   redirecting stdin from /dev/null

set -eux

run_test() {
   # testname is playbook name
   local testname=$1

   # The shenanigans with redirection and 'tee' are to capture STDOUT and
   # STDERR separately while still displaying both to the console
   { ansible-playbook -i 'localhost,' -c local "${testname}.yml" \
      > >(set +x; tee "${OUTFILE}.${testname}.stdout"); } \
      2> >(set +x; tee "${OUTFILE}.${testname}.stderr" >&2) 0</dev/null

   sed -i -e 's/ *$//' "${OUTFILE}.${testname}.stdout"
   sed -i -e 's/ *$//' "${OUTFILE}.${testname}.stderr"

   # Scrub deprication warning that shows up in Python 2.6 on CentOS 6
   sed -i -e '/RandomPool_DeprecationWarning/d' "${OUTFILE}.${testname}.stderr"

   diff -u "${ORIGFILE}.${testname}.stdout" "${OUTFILE}.${testname}.stdout" || diff_failure
   diff -u "${ORIGFILE}.${testname}.stderr" "${OUTFILE}.${testname}.stderr" || diff_failure
}

diff_failure() {
   if [[ $INIT = 0 ]]; then
      echo "FAILURE...diff mismatch!"
      exit 1
   fi
}

cleanup() {
   if [[ $INIT = 0 ]]; then
      rm -f "${OUTFILE}."*
   fi
}

BASEFILE=assert_quiet.out

ORIGFILE="${BASEFILE}"
OUTFILE="${BASEFILE}.new"

trap 'cleanup' EXIT

# The --init flag will (re)generate the "good" output files used by the tests
INIT=0
if [[ ${1:-} == "--init" ]]; then
   shift
   OUTFILE=$ORIGFILE
   INIT=1
fi

# Force the 'default' callback plugin
export ANSIBLE_STDOUT_CALLBACK=default
# Disable color in output for consistency
export ANSIBLE_FORCE_COLOR=0
export ANSIBLE_NOCOLOR=1
# Disable retry files
export ANSIBLE_RETRY_FILES_ENABLED=0

run_test quiet
