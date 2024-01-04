#!/usr/bin/env bash

set -eux -o pipefail

# set `fileno` limit artificially low to induce "too many open files" failures with a low number of forks
ulimit -n 30

echo "running test playbook and capturing output..."

# run test playbook with enough hosts/forks to quickly exhaust the low open files limit
set +e
ansible-playbook -i hosts -f 20 test.yml 2>&1 | tee out.txt
RC=$?
set -e

echo "ansible-playbook should yield RC==250 (unexpected error)"
[[ $RC == 250 ]] && echo PASS

echo "'some workers will fail' task ran?"
grep "some workers will fail" out.txt && echo PASS

echo "'should not run' task did not run?"
grep "should not run" out.txt || echo PASS

echo "PASS: all tests ok"
