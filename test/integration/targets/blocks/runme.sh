#!/usr/bin/env bash

set -eux

# This test does not use "$@" to avoid further increasing the verbosity beyond what is required for the test.
# Increasing verbosity from -vv to -vvv can increase the line count from ~400 to ~9K on our centos6 test container.

# remove old output log
rm -f block_test.out
# run the test and check to make sure the right number of completions was logged
ansible-playbook -vv main.yml -i ../../inventory | tee block_test.out
env python -c \
    'import sys, re; sys.stdout.write(re.sub("\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", sys.stdin.read()))' \
    <block_test.out >block_test_wo_colors.out
[ "$(grep -c 'TEST COMPLETE' block_test.out)" = "$(grep -E '^[0-9]+ plays in' block_test_wo_colors.out | cut -f1 -d' ')" ]
# cleanup the output log again, to make sure the test is clean
rm -f block_test.out block_test_wo_colors.out
# run test with free strategy and again count the completions
ansible-playbook -vv main.yml -i ../../inventory -e test_strategy=free | tee block_test.out
env python -c \
    'import sys, re; sys.stdout.write(re.sub("\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", sys.stdin.read()))' \
    <block_test.out >block_test_wo_colors.out
[ "$(grep -c 'TEST COMPLETE' block_test.out)" = "$(grep -E '^[0-9]+ plays in' block_test_wo_colors.out | cut -f1 -d' ')" ]
# cleanup the output log again, to make sure the test is clean
rm -f block_test.out block_test_wo_colors.out
# run test with host_pinned strategy and again count the completions
ansible-playbook -vv main.yml -i ../../inventory -e test_strategy=host_pinned | tee block_test.out
env python -c \
    'import sys, re; sys.stdout.write(re.sub("\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", sys.stdin.read()))' \
    <block_test.out >block_test_wo_colors.out
[ "$(grep -c 'TEST COMPLETE' block_test.out)" = "$(grep -E '^[0-9]+ plays in' block_test_wo_colors.out | cut -f1 -d' ')" ]

# run test that includes tasks that fail inside a block with always
rm -f block_test.out block_test_wo_colors.out
ansible-playbook -vv block_fail.yml -i ../../inventory | tee block_test.out
env python -c \
    'import sys, re; sys.stdout.write(re.sub("\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", sys.stdin.read()))' \
    <block_test.out >block_test_wo_colors.out
[ "$(grep -c 'TEST COMPLETE' block_test.out)" = "$(grep -E '^[0-9]+ plays in' block_test_wo_colors.out | cut -f1 -d' ')" ]

ansible-playbook -vv block_rescue_vars.yml

# https://github.com/ansible/ansible/issues/70000
set +e
exit_code=0
ansible-playbook -vv always_failure_with_rescue_rc.yml > rc_test.out || exit_code=$?
set -e
cat rc_test.out
[ $exit_code -eq 2 ]
[ "$(grep -c 'Failure in block' rc_test.out )" -eq 1 ]
[ "$(grep -c 'Rescue' rc_test.out )" -eq 1 ]
[ "$(grep -c 'Failure in always' rc_test.out )" -eq 1 ]
[ "$(grep -c 'DID NOT RUN' rc_test.out )" -eq 0 ]
rm -f rc_test_out

set +e
exit_code=0
ansible-playbook -vv always_no_rescue_rc.yml > rc_test.out || exit_code=$?
set -e
cat rc_test.out
[ $exit_code -eq 2 ]
[ "$(grep -c 'Failure in block' rc_test.out )" -eq 1 ]
[ "$(grep -c 'Always' rc_test.out )" -eq 1 ]
[ "$(grep -c 'DID NOT RUN' rc_test.out )" -eq 0 ]
rm -f rc_test.out

set +e
exit_code=0
ansible-playbook -vv always_failure_no_rescue_rc.yml > rc_test.out || exit_code=$?
set -e
cat rc_test.out
[ $exit_code -eq 2 ]
[ "$(grep -c 'Failure in block' rc_test.out )" -eq 1 ]
[ "$(grep -c 'Failure in always' rc_test.out )" -eq 1 ]
[ "$(grep -c 'DID NOT RUN' rc_test.out )" -eq 0 ]
rm -f rc_test.out

# https://github.com/ansible/ansible/issues/71306
set +e
exit_code=0
ansible-playbook -i host1,host2 -vv issue71306.yml > rc_test.out || exit_code=$?
set -e
cat rc_test.out
[ $exit_code -eq 0 ]
rm -f rc_test_out

# https://github.com/ansible/ansible/issues/29047
ansible-playbook -vv issue29047.yml -i ../../inventory

# https://github.com/ansible/ansible/issues/61253
ansible-playbook -vv block_in_rescue.yml -i ../../inventory > rc_test.out
cat rc_test.out
[ "$(grep -c 'rescued=3' rc_test.out)" -eq 1 ]
[ "$(grep -c 'failed=0' rc_test.out)" -eq 1 ]
rm -f rc_test.out

ansible-playbook unsafe_failed_task.yml "$@"

ansible-playbook finalized_task.yml "$@"
