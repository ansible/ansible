#!/usr/bin/env bash

set -eux

# Get the system temp directory (platform-independent)
TEMP_DIR=$($ANSIBLE_TEST_PYTHON_INTERPRETER -c "import tempfile; print(tempfile.gettempdir())")

test_default_temp_directory() {
    echo "=== Test 1: Stacktrace dump to default temp directory ==="
    echo "Using temp directory: $TEMP_DIR"

    # Start ansible-playbook in background with a long-running task
    ansible-playbook -i inventory playbook.yml &
    local ANSIBLE_PID
    ANSIBLE_PID=$!

    # Give it time to start executing and spawn workers
    sleep 2

    # Find all subprocess PIDs
    local CHILD_PIDS
    CHILD_PIDS=$(pgrep -P $ANSIBLE_PID 2>/dev/null || true)

    # Send SIGUSR1 signal to main process and all children
    kill -SIGUSR1 $ANSIBLE_PID
    # shellcheck disable=SC2086
    for child_pid in $CHILD_PIDS; do
        kill -SIGUSR1 $child_pid 2>/dev/null || true
    done

    # Give it time to write the files
    sleep 1

    # Find the stacktrace file for main process in temp directory
    local STACKTRACE_FILE
    STACKTRACE_FILE=$(find -L "$TEMP_DIR" -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

    if [[ -z "$STACKTRACE_FILE" ]]; then
        echo "FAIL: Stacktrace file not found in $TEMP_DIR for main process"
        kill $ANSIBLE_PID 2>/dev/null || true
        exit 1
    fi

    echo "Found stacktrace file for main process: $STACKTRACE_FILE"

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

    # Check for child process stacktrace files
    local CHILD_PIDS_COUNT=0
    local CHILD_FILES_FOUND=0
    for child_pid in $CHILD_PIDS; do
        CHILD_PIDS_COUNT=$((CHILD_PIDS_COUNT + 1))
        local CHILD_FILE
        CHILD_FILE=$(find -L "$TEMP_DIR" -name "ansible-${child_pid}.debug" 2>/dev/null | head -1)
        if [[ -n "$CHILD_FILE" ]]; then
            echo "Found stacktrace file for child process $child_pid: $CHILD_FILE"
            CHILD_FILES_FOUND=$((CHILD_FILES_FOUND + 1))
            rm -f "$CHILD_FILE"
        fi
    done

    if [[ $CHILD_PIDS_COUNT -gt 0 ]] && [[ $CHILD_FILES_FOUND -ne $CHILD_PIDS_COUNT ]]; then
        echo "FAIL: Expected stacktrace files for all $CHILD_PIDS_COUNT child processes, but found only $CHILD_FILES_FOUND"
        kill $ANSIBLE_PID 2>/dev/null || true
        exit 1
    else
        echo "Found stacktrace files for $CHILD_FILES_FOUND child process(es)"
    fi

    # Clean up
    kill $ANSIBLE_PID 2>/dev/null || true
    wait $ANSIBLE_PID 2>/dev/null || true
    rm -f "$STACKTRACE_FILE"

    echo "Test 1 PASSED"
}

test_custom_directory() {
    echo "=== Test 2: Stacktrace dump to custom directory ==="

    # Create custom directory
    local CUSTOM_DIR
    CUSTOM_DIR=$(mktemp -d)
    export ANSIBLE_STACKTRACE_DIR="$CUSTOM_DIR"

    # Start ansible-playbook in background
    ansible-playbook -i inventory playbook.yml &
    local ANSIBLE_PID
    ANSIBLE_PID=$!

    # Give it time to start executing and spawn workers
    sleep 2

    # Find all subprocess PIDs
    local CHILD_PIDS
    CHILD_PIDS=$(pgrep -P $ANSIBLE_PID 2>/dev/null || true)

    # Send SIGUSR1 signal to main process and all children
    kill -SIGUSR1 $ANSIBLE_PID
    # shellcheck disable=SC2086
    for child_pid in $CHILD_PIDS; do
        kill -SIGUSR1 $child_pid 2>/dev/null || true
    done

    # Give it time to write the file
    sleep 1

    # Verify file is in custom directory
    local STACKTRACE_FILE="${CUSTOM_DIR}/ansible-${ANSIBLE_PID}.debug"

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

    # Check for child process stacktrace files in custom directory
    local CHILD_PIDS_COUNT=0
    local CHILD_FILES_FOUND=0
    for child_pid in $CHILD_PIDS; do
        CHILD_PIDS_COUNT=$((CHILD_PIDS_COUNT + 1))
        local CHILD_FILE="${CUSTOM_DIR}/ansible-${child_pid}.debug"
        if [[ -f "$CHILD_FILE" ]]; then
            echo "Found stacktrace file for child process $child_pid in custom directory"
            CHILD_FILES_FOUND=$((CHILD_FILES_FOUND + 1))
        fi
    done

    if [[ $CHILD_PIDS_COUNT -gt 0 ]] && [[ $CHILD_FILES_FOUND -ne $CHILD_PIDS_COUNT ]]; then
        echo "FAIL: Expected stacktrace files for all $CHILD_PIDS_COUNT child processes in custom directory, but found only $CHILD_FILES_FOUND"
        kill $ANSIBLE_PID 2>/dev/null || true
        rm -rf "$CUSTOM_DIR"
        exit 1
    else
        echo "Found stacktrace files for $CHILD_FILES_FOUND child process(es) in custom directory"
    fi

    # Clean up
    kill $ANSIBLE_PID 2>/dev/null || true
    wait $ANSIBLE_PID 2>/dev/null || true
    rm -rf "$CUSTOM_DIR"

    echo "Test 2 PASSED"
}

test_multiple_signals_append() {
    echo "=== Test 3: Multiple SIGUSR1 signals append to file ==="

    # Unset custom directory from Test 2
    unset ANSIBLE_STACKTRACE_DIR

    # Start ansible-playbook in background
    ansible-playbook -i inventory playbook.yml &
    local ANSIBLE_PID
    ANSIBLE_PID=$!

    # Give it time to start executing
    sleep 2

    # Send SIGUSR1 signal twice
    kill -SIGUSR1 $ANSIBLE_PID
    sleep 1
    kill -SIGUSR1 $ANSIBLE_PID
    sleep 1

    # Find the stacktrace file
    local STACKTRACE_FILE
    STACKTRACE_FILE=$(find -L "$TEMP_DIR" -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

    if [[ -z "$STACKTRACE_FILE" ]]; then
        echo "FAIL: Stacktrace file not found"
        kill $ANSIBLE_PID 2>/dev/null || true
        exit 1
    fi

    # Count the number of stacktrace entries (should be 2)
    local COUNT
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
}

test_invalid_directory() {
    echo "=== Test 4: Invalid ANSIBLE_STACKTRACE_DIR gracefully fails ==="

    # Set an invalid/nonexistent directory path
    export ANSIBLE_STACKTRACE_DIR="/nonexistent/invalid/path"

    # Start ansible-playbook in background
    ansible-playbook -i inventory playbook.yml &
    local ANSIBLE_PID
    ANSIBLE_PID=$!

    # Give it time to start executing and spawn workers
    sleep 2

    # Find all subprocess PIDs
    local CHILD_PIDS
    CHILD_PIDS=$(pgrep -P $ANSIBLE_PID 2>/dev/null || true)

    # Send SIGUSR1 signal to main process and all children
    kill -SIGUSR1 $ANSIBLE_PID
    # shellcheck disable=SC2086
    for child_pid in $CHILD_PIDS; do
        kill -SIGUSR1 $child_pid 2>/dev/null || true
    done

    # Give it time to (fail to) write files
    sleep 1

    # Verify ansible is still running (didn't crash)
    if ! ps -p $ANSIBLE_PID >/dev/null 2>&1; then
        echo "FAIL: Ansible process crashed when trying to write to invalid directory"
        exit 1
    fi

    echo "Ansible process still running - signal handler did not crash"

    # Verify no stacktrace files were created in the invalid directory
    # (we can't check the invalid path since it doesn't exist, but we can verify
    # no files were created in the default temp directory)
    local STACKTRACE_FILE
    STACKTRACE_FILE=$(find -L "$TEMP_DIR" -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

    if [[ -n "$STACKTRACE_FILE" ]]; then
        echo "FAIL: Unexpected stacktrace file found in default temp directory: $STACKTRACE_FILE"
        kill $ANSIBLE_PID 2>/dev/null || true
        exit 1
    fi

    echo "No stacktrace files created with invalid directory - signal handler failed gracefully"

    # Clean up
    kill $ANSIBLE_PID 2>/dev/null || true
    wait $ANSIBLE_PID 2>/dev/null || true

    echo "Test 4 PASSED"
}

# Run all tests
test_default_temp_directory
test_custom_directory
test_multiple_signals_append
test_invalid_directory

echo "=== All tests PASSED ==="
