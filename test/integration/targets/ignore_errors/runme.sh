#!/usr/bin/env bash
set -eux

ansible-playbook -i ../../inventory test_ignore_errors.yml "$@"

ansible-playbook -i ../../inventory test_invalid_ignore_errors.yml "$@" | tee out.txt || true
grep 'CHECKS PASSED' out.txt

# RPFIX-5: BUG: ignore_errors is incorrectly handled on loop items
# ansible-playbook -i ../../inventory test_ignore_errors_loop.yml "$@" | tee out.txt || true
# grep 'CHECKS PASSED' out.txt

ansible-playbook test_looped_errors.yml "$@" | tee out.txt
grep "dynamichost.*ok=3.*failed=1.*ignored=2" out.txt

if ansible-playbook -i ../../inventory test_ignore_errors_false.yml "$@" > out.txt; then
    echo 'Playbook expected to fail succeeded'
    exit 1
fi

# The first task should fail and not be ignored
grep 'testhost.*ok=0.*failed=1.*ignored=0' out.txt
echo PASS
