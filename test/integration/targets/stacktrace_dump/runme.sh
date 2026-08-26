#!/usr/bin/env bash

set -eux

# Get the debug directory where stacktrace files are written
DEBUG_DIR="${ANSIBLE_HOME:-$HOME/.ansible}/debug"

test_controller_debug_directory() {
    echo "=== Test: Stacktrace dump to debug directory ==="
    echo "Using debug directory: $DEBUG_DIR"

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

    # Find the stacktrace file for main process in debug directory
    local STACKTRACE_FILE
    STACKTRACE_FILE=$(find -L "$DEBUG_DIR" -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

    if [[ -z "$STACKTRACE_FILE" ]]; then
        echo "FAIL: Stacktrace file not found in $DEBUG_DIR for main process"
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
        CHILD_FILE=$(find -L "$DEBUG_DIR" -name "ansible-${child_pid}.debug" 2>/dev/null | head -1)
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

    echo "Test PASSED"
}

test_multiple_signals_append() {
    echo "=== Test: Multiple SIGUSR1 signals append to file ==="

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
    STACKTRACE_FILE=$(find -L "$DEBUG_DIR" -name "ansible-${ANSIBLE_PID}.debug" 2>/dev/null | head -1)

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

    echo "Test PASSED"
}

test_symlink_not_followed() {
    echo "=== Test: Symlink at stacktrace path is not followed ==="

    # Start ansible-playbook in background
    ansible-playbook -i inventory playbook.yml &
    local ANSIBLE_PID
    ANSIBLE_PID=$!

    # Give it time to start executing and pre-create the debug directory
    sleep 2

    # Pre-plant a symlink at the predictable stacktrace path pointing at a canary
    # file. A correct handler must refuse to follow it (O_NOFOLLOW).
    local CANARY
    CANARY=$(mktemp)
    rm -f "$CANARY"
    local SYMLINK="$DEBUG_DIR/ansible-${ANSIBLE_PID}.debug"
    rm -f "$SYMLINK"
    ln -s "$CANARY" "$SYMLINK"

    # Signal the process to trigger the stacktrace write
    kill -SIGUSR1 $ANSIBLE_PID
    sleep 1

    # The canary must NOT have been created/written through the symlink
    if [[ -e "$CANARY" ]]; then
        echo "FAIL: stacktrace write followed the symlink and wrote to $CANARY"
        kill $ANSIBLE_PID 2>/dev/null || true
        rm -f "$CANARY" "$SYMLINK"
        exit 1
    fi

    # The planted symlink should remain a symlink (open failed, nothing replaced it)
    if [[ ! -L "$SYMLINK" ]]; then
        echo "FAIL: expected the planted symlink to remain untouched at $SYMLINK"
        kill $ANSIBLE_PID 2>/dev/null || true
        rm -f "$CANARY" "$SYMLINK"
        exit 1
    fi

    echo "Symlink was not followed and canary was not written"

    # Clean up
    kill $ANSIBLE_PID 2>/dev/null || true
    wait $ANSIBLE_PID 2>/dev/null || true
    rm -f "$CANARY" "$SYMLINK"

    echo "Test PASSED"
}

# Run all tests
test_controller_debug_directory
test_multiple_signals_append
test_symlink_not_followed

echo "=== All tests PASSED ==="
