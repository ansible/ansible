#!/usr/bin/env bash

set -eux

# Test max_fail_percentage: 0 causes immediate failure
set +e
ansible-playbook -i inventory.ini "$@" test-standard-0.yml 2>&1 | tee out.txt
rc=$?
set -e

# Verify play stopped when threshold exceeded
if grep -q 'SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task after threshold should not have executed"
    exit 1
fi

rm -f out.txt

# Test max_fail_percentage: 50 threshold behavior
set +e
ansible-playbook -i inventory.ini "$@" test-standard-50.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 2: 40% failure (5/10), allows continuation, 6 hosts remain
[ "$(grep -c 'SHOULD_EXECUTE_6_TIMES' out.txt)" -eq 6 ]

# Play 3: 50% failure (3/6), allows continuation, 3 hosts remain
[ "$(grep -c 'SHOULD_EXECUTE_3_TIMES' out.txt)" -eq 3 ]

# Play 4: 67% failure (2/3), above threshold so it should fail
if grep -q 'SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when all hosts failed"
    exit 1
fi

rm -f out.txt

# Test max_fail_percentage: 100 allows all failures
set +e
ansible-playbook -i inventory.ini "$@" test-standard-100.yml 2>&1 | tee out.txt
rc=$?
set -e

# Verify tasks executed on remaining hosts when 1 failed
[ "$(grep -c 'SHOULD_EXECUTE_9_TIMES' out.txt)" -eq 9 ]

# Verify tasks executed on remaining hosts when 5 failed
[ "$(grep -c 'SHOULD_EXECUTE_5_TIMES' out.txt)" -eq 5 ]

# Verify tasks didn't execute when all hosts failed
if grep -q 'SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when all hosts failed"
    exit 1
fi

rm -f out.txt

# Test unreachable hosts with 0% threshold
set +e
ansible-playbook -i inventory.ini "$@" test-unreachable-0.yml 2>&1 | tee out.txt
rc=$?
set -e

# Verify play stopped when 1 unreachable exceeded 0% threshold
if grep -q 'SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when unreachable threshold exceeded"
    exit 1
fi

rm -f out.txt

# Test unreachable hosts with 50% threshold
set +e
ansible-playbook -i inventory.ini "$@" test-unreachable-50.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: 1 unreachable/5 = 20% < 50%, continues
[ "$(grep -c 'SHOULD_EXECUTE_4_TIMES' out.txt)" -eq 4 ]

# Play 2: 1 failed + 1 unreachable = 2/4 = 50%, continues
[ "$(grep -c 'SHOULD_EXECUTE_2_TIMES' out.txt)" -eq 2 ]

# Play 3: 1 failed + 2 unreachable = 3/5 = 60% > 50%, breaks
if grep -q 'SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when unreachable+failed exceeded threshold"
    exit 1
fi

rm -f out.txt

# Test unreachable hosts with 100% threshold
set +e
ansible-playbook -i inventory.ini "$@" test-unreachable-100.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: 1 unreachable/4 = 25% < 100%, continues
[ "$(grep -c 'SHOULD_EXECUTE_3_TIMES' out.txt)" -eq 3 ]

# Play 2: 2/2 = 100%, all hosts unreachable, no hosts left
if grep -q 'SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when no hosts remain"
    exit 1
fi

rm -f out.txt

# Test blocks - basic behavior with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-blocks-basic.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: Block threshold not exceeded (2/5 = 40% < 50%)
[ "$(grep -c 'BLOCK_THRESHOLD_NOT_EXCEEDED' out.txt)" -eq 3 ]
[ "$(grep -c 'AFTER_BLOCK_NOT_EXCEEDED' out.txt)" -eq 3 ]

# Play 2: Block threshold exceeded (2/3 = 67% > 50%)
if grep -q 'BLOCK_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Block task should not execute when threshold exceeded"
    exit 1
fi
if grep -q 'AFTER_BLOCK_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task after block should not execute when threshold exceeded"
    exit 1
fi

rm -f out.txt

# Test blocks - rescue behavior with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-blocks-rescue.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: Rescue should execute even when threshold exceeded in main block
[ "$(grep -c 'RESCUE_EXECUTED_AFTER_THRESHOLD' out.txt)" -eq 4 ]
[ "$(grep -c 'AFTER_RESCUE_BLOCK' out.txt)" -eq 4 ]
if grep -q 'MAIN_BLOCK_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Main block should not continue after threshold exceeded"
    exit 1
fi

# Play 2: Threshold exceeded in rescue block
if grep -q 'RESCUE_THRESHOLD_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Rescue should not continue after threshold exceeded"
    exit 1
fi
if grep -q 'AFTER_RESCUE_THRESHOLD_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task after rescue failure should not execute"
    exit 1
fi

rm -f out.txt

# Test blocks - recovery behavior with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-blocks-recovery.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: Recovery in rescue
[ "$(grep -c 'RECOVERY_RESCUE_EXECUTED' out.txt)" -eq 5 ]
[ "$(grep -c 'AFTER_RECOVERY_EXECUTED' out.txt)" -eq 5 ]

# Play 2: New play after recovery sees all hosts
[ "$(grep -c 'NEW_PLAY_AFTER_RECOVERY' out.txt)" -eq 5 ]

rm -f out.txt

# Test blocks - always behavior with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-blocks-always.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: Always executes even when threshold exceeded
[ "$(grep -c 'ALWAYS_EXECUTED_AFTER_THRESHOLD' out.txt)" -eq 4 ]
[ "$(grep -c 'AFTER_ALWAYS_BLOCK' out.txt)" -eq 4 ]
if grep -q 'ALWAYS_MAIN_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Main block should not continue after threshold exceeded"
    exit 1
fi

# Play 2: Threshold exceeded in always block
[ "$(grep -c 'ALWAYS_THRESHOLD_MAIN_BLOCK' out.txt)" -eq 4 ]
if grep -q 'ALWAYS_THRESHOLD_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Always should not continue after threshold exceeded"
    exit 1
fi
if grep -q 'AFTER_ALWAYS_THRESHOLD_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task after always failure should not execute"
    exit 1
fi

rm -f out.txt

# Test ignore_errors interaction with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-ignore-errors.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: 3 failures ignored, should continue on all hosts
[ "$(grep -c 'IGNORE_ERRORS_ALL_EXECUTED' out.txt)" -eq 5 ]

# Play 2: 2 ignored failures + 1 real failure, should continue on 4 hosts
[ "$(grep -c 'IGNORE_ERRORS_MIXED_EXECUTED' out.txt)" -eq 4 ]

# Play 3: 1 ignored + 2 real failures exceed threshold
if grep -q 'IGNORE_ERRORS_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when real failures exceeded threshold"
    exit 1
fi

rm -f out.txt

# Test ignore_unreachable interaction with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-ignore-unreachable.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: 2 unreachable ignored, should execute on all reachable hosts
[ "$(grep -c 'IGNORE_UNREACHABLE_ALL_EXECUTED' out.txt)" -eq 3 ]

# Play 2: 1 unreachable ignored + 1 failure, should execute on 2 hosts
[ "$(grep -c 'IGNORE_UNREACHABLE_MIXED_EXECUTED' out.txt)" -eq 2 ]

# Play 3: 1 unreachable ignored + 2 failures = 50%, should execute on 1 host
[ "$(grep -c 'IGNORE_UNREACHABLE_THRESHOLD_EXECUTED' out.txt)" -eq 1 ]

# Play 4: 1 unreachable ignored + 3 failures exceed threshold
if grep -q 'IGNORE_UNREACHABLE_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when real failures exceeded threshold"
    exit 1
fi

rm -f out.txt

# Test recovery interaction with max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-recovery.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: Recovered hosts fail again, exceeding threshold
if grep -q 'RECOVERY_SHOULD_NOT_EXECUTE_THRESHOLD_EXCEEDED' out.txt; then
    echo "ERROR: Task should not execute when threshold exceeded after recovery"
    exit 1
fi
if grep -q 'RECOVERY_SHOULD_NOT_EXECUTE_IN_BLOCK' out.txt; then
    echo "ERROR: Block should not continue after threshold exceeded"
    exit 1
fi

# Play 2: Recovery in rescue after threshold exceeded
[ "$(grep -c 'RECOVERY_RESCUE_EXECUTED' out.txt)" -eq 3 ]

# Play 3: Recovered hosts available in next play
[ "$(grep -c 'RECOVERY_NEXT_PLAY_EXECUTED' out.txt)" -eq 3 ]

rm -f out.txt

# Test any_errors_fatal takes precedence over max_fail_percentage
set +e
ansible-playbook -i inventory.ini "$@" test-any-errors-fatal.yml 2>&1 | tee out.txt
rc=$?
set -e

# Play 1: any_errors_fatal=true with max_fail_percentage=100%, 1 failure should stop
if grep -q 'ANY_ERRORS_FATAL_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when any_errors_fatal stops play"
    exit 1
fi

# Play 2: any_errors_fatal=true with max_fail_percentage=50%, 1 failure should stop
if grep -q 'ANY_ERRORS_FATAL_LOW_PERCENT_SHOULD_NOT_EXECUTE' out.txt; then
    echo "ERROR: Task should not execute when any_errors_fatal stops play"
    exit 1
fi

# Play 3: any_errors_fatal=false, max_fail_percentage should work normally
[ "$(grep -c 'ANY_ERRORS_FATAL_EXECUTED_WHEN_FALSE' out.txt)" -eq 2 ]

rm -f out.txt
