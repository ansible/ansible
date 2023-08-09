#!/usr/bin/env bash

set -eu

ansible-playbook playbook.yml -i ../../inventory "$@"

cleanup() {
    rm -f out.txt
    # Background process should stop in a few more seconds
    sleep 4
    if ps -p "$bg_pid" > /dev/null; then
        echo "Terminating background process (PID: $bg_pid)..."
        kill "$bg_pid"
    fi
}

trap cleanup EXIT

# The presence of the -u option guarantees that unbuffered I/O is available.
# (https://pubs.opengroup.org/onlinepubs/9699919799.2018edition/utilities/cat.html)
# This makes it easy to see when explicit flushes occur in Display.
( ansible-playbook -i ../../inventory test_loop_item_display.yml "$@" | cat -u ) > out.txt &
bg_pid=$!

echo "Sleep > 5s to verify item 1 results have been flushed before the task is complete"
sleep 8

if ! grep 'item=1' < out.txt; then
    echo "Error: Failed to grep 'item=1'"
    exit 1
fi

if grep 'item=2' < out.txt; then
    echo "Error: expected bg proc to take at least 10 seconds for 'item=2'"
    exit 1
fi
