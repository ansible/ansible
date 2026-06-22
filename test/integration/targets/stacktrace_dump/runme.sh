#!/usr/bin/env bash

set -eux

# Test 1: Default behavior - stacktrace written to temp directory
echo "=== Test 1: Stacktrace dump to default temp directory ==="

# Start ansible-playbook in background with a long-running task
ansible-playbook -i inventory playbook.yml &
ANSIBLE_PID=$!

# Give it time to start executing
sleep 2

# Send SIGUSR1 signal to trigger stacktrace dump
kill -SIGUSR1 $ANSIBLE_PID

# Give it time to write the file
sleep 1

# Find the stacktrace file in temp directory
STACKTRACE_FILE=$(find /tmp -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

if [[ -z "$STACKTRACE_FILE" ]]; then
    echo "FAIL: Stacktrace file not found in /tmp"
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

echo "Found stacktrace file: $STACKTRACE_FILE"

# Verify file contains expected content
if ! grep -q "Process ${ANSIBLE_PID} stacktrace" "$STACKTRACE_FILE"; then
    echo "FAIL: Stacktrace file missing process stacktrace header"
    cat "$STACKTRACE_FILE"
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

if ! grep -q "Thread stacktraces" "$STACKTRACE_FILE"; then
    echo "FAIL: Stacktrace file missing thread stacktraces header"
    cat "$STACKTRACE_FILE"
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

# Clean up
kill $ANSIBLE_PID 2>/dev/null || true
wait $ANSIBLE_PID 2>/dev/null || true
rm -f "$STACKTRACE_FILE"

echo "Test 1 PASSED"

# Test 2: Custom directory via ANSIBLE_STACKTRACE_DIR
echo "=== Test 2: Stacktrace dump to custom directory ==="

# Create custom directory
CUSTOM_DIR=$(mktemp -d)
export ANSIBLE_STACKTRACE_DIR="$CUSTOM_DIR"

# Start ansible-playbook in background
ansible-playbook -i inventory playbook.yml &
ANSIBLE_PID=$!

# Give it time to start executing
sleep 2

# Send SIGUSR1 signal
kill -SIGUSR1 $ANSIBLE_PID

# Give it time to write the file
sleep 1

# Verify file is in custom directory
STACKTRACE_FILE="${CUSTOM_DIR}/ansible-${ANSIBLE_PID}.debug"

if [[ ! -f "$STACKTRACE_FILE" ]]; then
    echo "FAIL: Stacktrace file not found in custom directory: $STACKTRACE_FILE"
    ls -la "$CUSTOM_DIR" || true
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

echo "Found stacktrace file in custom directory: $STACKTRACE_FILE"

# Verify file contains expected content
if ! grep -q "Process ${ANSIBLE_PID} stacktrace" "$STACKTRACE_FILE"; then
    echo "FAIL: Stacktrace file missing process stacktrace header"
    cat "$STACKTRACE_FILE"
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

# Clean up
kill $ANSIBLE_PID 2>/dev/null || true
wait $ANSIBLE_PID 2>/dev/null || true
rm -rf "$CUSTOM_DIR"

echo "Test 2 PASSED"

# Test 3: Multiple signals append to same file
echo "=== Test 3: Multiple SIGUSR1 signals append to file ==="

# Unset custom directory from Test 2
unset ANSIBLE_STACKTRACE_DIR

# Start ansible-playbook in background
ansible-playbook -i inventory playbook.yml &
ANSIBLE_PID=$!

# Give it time to start executing
sleep 2

# Send SIGUSR1 signal twice
kill -SIGUSR1 $ANSIBLE_PID
sleep 1
kill -SIGUSR1 $ANSIBLE_PID
sleep 1

# Find the stacktrace file
STACKTRACE_FILE=$(find /tmp -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

if [[ -z "$STACKTRACE_FILE" ]]; then
    echo "FAIL: Stacktrace file not found"
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

# Count the number of stacktrace entries (should be 2)
COUNT=$(grep -c "Process ${ANSIBLE_PID} stacktrace" "$STACKTRACE_FILE")

if [[ "$COUNT" -ne 2 ]]; then
    echo "FAIL: Expected 2 stacktrace entries, found $COUNT"
    cat "$STACKTRACE_FILE"
    kill $ANSIBLE_PID 2>/dev/null || true
    exit 1
fi

echo "Found $COUNT stacktrace entries as expected"

# Clean up
kill $ANSIBLE_PID 2>/dev/null || true
wait $ANSIBLE_PID 2>/dev/null || true
rm -f "$STACKTRACE_FILE"

echo "Test 3 PASSED"

echo "=== All tests PASSED ==="
