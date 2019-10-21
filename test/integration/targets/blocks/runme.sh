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
