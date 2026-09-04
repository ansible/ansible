#!/usr/bin/env bash

set -eu

# Track test results by file
declare -A TEST_RESULTS

function run_test() {
    local test_file="$1"
    local test_name="${test_file%.yml}"

    echo -n "Testing ${test_file}... "

    set +e
    ansible-playbook -i inventory.ini "$@" "${test_file}" > out.txt 2>&1
    local rc=$?
    set -e

    return 0  # Don't exit on test failure
}

function check_result() {
    local test_name="$1"
    local check_type="$2"
    local pattern="$3"
    local expected_count="${4:-0}"
    local mode="${5:-exact}"  # exact, none, or any

    if [ "$mode" = "none" ]; then
        if grep -q "$pattern" out.txt; then
            TEST_RESULTS["$test_name"]+="FAIL: Found unexpected '$pattern'\n"
            return 1
        fi
    elif [ "$mode" = "exact" ]; then
        local actual=$(grep -c "$pattern" out.txt 2>/dev/null || true)
        if [ -z "$actual" ] || [ "$actual" = "" ]; then
            actual=0
        fi
        if [ "$actual" -ne "$expected_count" ] 2>/dev/null; then
            TEST_RESULTS["$test_name"]+="FAIL: Expected $expected_count of '$pattern', got $actual\n"
            return 1
        fi
    fi
    return 0
}

# Test: test-standard-0.yml
run_test test-standard-0.yml
TEST_RESULTS["test-standard-0"]=""
check_result "test-standard-0" "none" "SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-standard-0]}" ]; then
    TEST_RESULTS["test-standard-0"]="PASS"
fi
rm -f out.txt

# Test: test-standard-50.yml
run_test test-standard-50.yml
TEST_RESULTS["test-standard-50"]=""
check_result "test-standard-50" "exact" "SHOULD_EXECUTE_6_TIMES" 6 || true
check_result "test-standard-50" "exact" "SHOULD_EXECUTE_3_TIMES" 3 || true
check_result "test-standard-50" "none" "SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-standard-50]}" ]; then
    TEST_RESULTS["test-standard-50"]="PASS"
fi
rm -f out.txt

# Test: test-standard-100.yml
run_test test-standard-100.yml
TEST_RESULTS["test-standard-100"]=""
check_result "test-standard-100" "exact" "SHOULD_EXECUTE_9_TIMES" 9 || true
check_result "test-standard-100" "exact" "SHOULD_EXECUTE_5_TIMES" 5 || true
check_result "test-standard-100" "none" "SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-standard-100]}" ]; then
    TEST_RESULTS["test-standard-100"]="PASS"
fi
rm -f out.txt

# Test: test-unreachable-0.yml
run_test test-unreachable-0.yml
TEST_RESULTS["test-unreachable-0"]=""
check_result "test-unreachable-0" "none" "SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-unreachable-0]}" ]; then
    TEST_RESULTS["test-unreachable-0"]="PASS"
fi
rm -f out.txt

# Test: test-unreachable-50.yml
run_test test-unreachable-50.yml
TEST_RESULTS["test-unreachable-50"]=""
check_result "test-unreachable-50" "exact" "SHOULD_EXECUTE_4_TIMES" 4 || true
check_result "test-unreachable-50" "exact" "SHOULD_EXECUTE_2_TIMES" 2 || true
check_result "test-unreachable-50" "none" "SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-unreachable-50]}" ]; then
    TEST_RESULTS["test-unreachable-50"]="PASS"
fi
rm -f out.txt

# Test: test-unreachable-100.yml
run_test test-unreachable-100.yml
TEST_RESULTS["test-unreachable-100"]=""
check_result "test-unreachable-100" "exact" "SHOULD_EXECUTE_3_TIMES" 3 || true
check_result "test-unreachable-100" "none" "SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-unreachable-100]}" ]; then
    TEST_RESULTS["test-unreachable-100"]="PASS"
fi
rm -f out.txt

# Test: test-blocks-basic.yml
run_test test-blocks-basic.yml
TEST_RESULTS["test-blocks-basic"]=""
check_result "test-blocks-basic" "exact" "BLOCK_THRESHOLD_NOT_EXCEEDED" 3 || true
check_result "test-blocks-basic" "exact" "AFTER_BLOCK_NOT_EXCEEDED" 3 || true
check_result "test-blocks-basic" "none" "BLOCK_SHOULD_NOT_EXECUTE" || true
check_result "test-blocks-basic" "none" "AFTER_BLOCK_SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-blocks-basic]}" ]; then
    TEST_RESULTS["test-blocks-basic"]="PASS"
fi
rm -f out.txt

# Test: test-blocks-rescue.yml
run_test test-blocks-rescue.yml
TEST_RESULTS["test-blocks-rescue"]=""
check_result "test-blocks-rescue" "exact" "RESCUE_EXECUTED_AFTER_THRESHOLD" 4 || true
check_result "test-blocks-rescue" "exact" "AFTER_RESCUE_BLOCK" 4 || true
check_result "test-blocks-rescue" "none" "MAIN_BLOCK_SHOULD_NOT_EXECUTE" || true
check_result "test-blocks-rescue" "none" "RESCUE_THRESHOLD_SHOULD_NOT_EXECUTE" || true
check_result "test-blocks-rescue" "none" "AFTER_RESCUE_THRESHOLD_SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-blocks-rescue]}" ]; then
    TEST_RESULTS["test-blocks-rescue"]="PASS"
fi
rm -f out.txt

# Test: test-blocks-recovery.yml
run_test test-blocks-recovery.yml
TEST_RESULTS["test-blocks-recovery"]=""
check_result "test-blocks-recovery" "exact" "RECOVERY_RESCUE_EXECUTED" 5 || true
check_result "test-blocks-recovery" "exact" "AFTER_RECOVERY_EXECUTED" 5 || true
check_result "test-blocks-recovery" "exact" "NEW_PLAY_AFTER_RECOVERY" 5 || true
if [ -z "${TEST_RESULTS[test-blocks-recovery]}" ]; then
    TEST_RESULTS["test-blocks-recovery"]="PASS"
fi
rm -f out.txt

# Test: test-blocks-always.yml
run_test test-blocks-always.yml
TEST_RESULTS["test-blocks-always"]=""
check_result "test-blocks-always" "exact" "ALWAYS_EXECUTED_AFTER_THRESHOLD" 4 || true
check_result "test-blocks-always" "exact" "AFTER_ALWAYS_BLOCK" 4 || true
check_result "test-blocks-always" "none" "ALWAYS_MAIN_SHOULD_NOT_EXECUTE" || true
check_result "test-blocks-always" "exact" "ALWAYS_THRESHOLD_MAIN_BLOCK" 4 || true
check_result "test-blocks-always" "none" "ALWAYS_THRESHOLD_SHOULD_NOT_EXECUTE" || true
check_result "test-blocks-always" "none" "AFTER_ALWAYS_THRESHOLD_SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-blocks-always]}" ]; then
    TEST_RESULTS["test-blocks-always"]="PASS"
fi
rm -f out.txt

# Test: test-ignore-errors.yml
run_test test-ignore-errors.yml
TEST_RESULTS["test-ignore-errors"]=""
check_result "test-ignore-errors" "exact" "IGNORE_ERRORS_ALL_EXECUTED" 5 || true
check_result "test-ignore-errors" "exact" "IGNORE_ERRORS_MIXED_EXECUTED" 4 || true
check_result "test-ignore-errors" "none" "IGNORE_ERRORS_SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-ignore-errors]}" ]; then
    TEST_RESULTS["test-ignore-errors"]="PASS"
fi
rm -f out.txt

# Test: test-ignore-unreachable.yml
run_test test-ignore-unreachable.yml
TEST_RESULTS["test-ignore-unreachable"]=""
check_result "test-ignore-unreachable" "exact" "IGNORE_UNREACHABLE_ALL_EXECUTED" 3 || true
check_result "test-ignore-unreachable" "exact" "IGNORE_UNREACHABLE_MIXED_EXECUTED" 2 || true
check_result "test-ignore-unreachable" "exact" "IGNORE_UNREACHABLE_THRESHOLD_EXECUTED" 1 || true
check_result "test-ignore-unreachable" "none" "IGNORE_UNREACHABLE_SHOULD_NOT_EXECUTE" || true
if [ -z "${TEST_RESULTS[test-ignore-unreachable]}" ]; then
    TEST_RESULTS["test-ignore-unreachable"]="PASS"
fi
rm -f out.txt

# Test: test-recovery.yml
run_test test-recovery.yml
TEST_RESULTS["test-recovery"]=""
check_result "test-recovery" "none" "RECOVERY_SHOULD_NOT_EXECUTE_THRESHOLD_EXCEEDED" || true
check_result "test-recovery" "none" "RECOVERY_SHOULD_NOT_EXECUTE_IN_BLOCK" || true
check_result "test-recovery" "exact" "RECOVERY_RESCUE_EXECUTED" 3 || true
check_result "test-recovery" "exact" "RECOVERY_NEXT_PLAY_EXECUTED" 3 || true
if [ -z "${TEST_RESULTS[test-recovery]}" ]; then
    TEST_RESULTS["test-recovery"]="PASS"
fi
rm -f out.txt

# Test: test-any-errors-fatal.yml
run_test test-any-errors-fatal.yml
TEST_RESULTS["test-any-errors-fatal"]=""
check_result "test-any-errors-fatal" "none" "ANY_ERRORS_FATAL_SHOULD_NOT_EXECUTE" || true
check_result "test-any-errors-fatal" "none" "ANY_ERRORS_FATAL_LOW_PERCENT_SHOULD_NOT_EXECUTE" || true
check_result "test-any-errors-fatal" "exact" "ANY_ERRORS_FATAL_EXECUTED_WHEN_FALSE" 2 || true
if [ -z "${TEST_RESULTS[test-any-errors-fatal]}" ]; then
    TEST_RESULTS["test-any-errors-fatal"]="PASS"
fi
rm -f out.txt

# Report results
echo ""
echo "========================================"
echo "TEST SUMMARY"
echo "========================================"

PASSED=()
FAILED=()

for test in test-standard-0 test-standard-50 test-standard-100 test-unreachable-0 test-unreachable-50 test-unreachable-100 test-blocks-basic test-blocks-rescue test-blocks-recovery test-blocks-always test-ignore-errors test-ignore-unreachable test-recovery test-any-errors-fatal; do
    result="${TEST_RESULTS[$test]}"
    if [ "$result" = "PASS" ]; then
        PASSED+=("$test")
        echo "✓ ${test}.yml"
    else
        FAILED+=("$test")
        echo "✗ ${test}.yml"
    fi
done

echo ""
echo "Passed: ${#PASSED[@]}/14"
echo "Failed: ${#FAILED[@]}/14"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "========================================"
    echo "FAILURE DETAILS"
    echo "========================================"
    for test in "${FAILED[@]}"; do
        echo ""
        echo "${test}.yml:"
        echo -e "${TEST_RESULTS[$test]}" | grep FAIL | sed 's/^/  /'
    done
    exit 1
fi

exit 0
