#!/usr/bin/env bash

set -eux

# export JUNIT_OUTPUT_DIR="$PWD/reports"

rm -rf reports
mkdir reports

ansible-playbook junit-callback-test.yml -i inventory "$@"
# Copy report to local directory
mv "$(find "$JUNIT_OUTPUT_DIR" -name "junit-callback-test-[0-9]*" | sort -r | head -1)" reports
# Remove classname and time
cat reports/junit-callback-test-[0-9]* | sed -e 's/time=".*"//' | sed -e 's/classname=".*"//' > reports/junit-callback-test.xml

JUNIT_TEST_CASE_PREFIX="JUNIT TASK PREFIX - " \
    ansible-playbook junit-callback-test-prefix.yml -i inventory "$@"
# # Compare with expected result
mv "$(find "$JUNIT_OUTPUT_DIR" -name "junit-callback-test-prefix-[0-9]*" | sort -r | head -1)" reports
# Remove classname and time
cat reports/junit-callback-test-prefix-[0-9]* | sed -e 's/time=".*"//' | sed -e 's/classname=".*"//' > reports/junit-callback-test-prefix.xml

JUNIT_TEST_CASE_PREFIX="JUNIT TASK PREFIX - " \
JUNIT_TEST_CASE_IGNORE_TEXT="JUNIT IGNORE THIS TASK" \
    ansible-playbook junit-callback-test-ignore.yml -i inventory "$@"
# Compare with expected result
mv "$(find "$JUNIT_OUTPUT_DIR" -name "junit-callback-test-ignore-[0-9]*" | sort -r | head -1)" reports
# Remove classname and time
cat reports/junit-callback-test-ignore-[0-9]* | sed -e 's/time=".*"//' | sed -e 's/classname=".*"//' > reports/junit-callback-test-ignore.xml

diff --ignore-space-change expected_reports/junit-callback-test.xml reports/junit-callback-test.xml
diff --ignore-space-change expected_reports/junit-callback-test-prefix.xml reports/junit-callback-test-prefix.xml
diff --ignore-space-change expected_reports/junit-callback-test-ignore.xml reports/junit-callback-test-ignore.xml