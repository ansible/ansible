#!/usr/bin/env bash

set -eux

./posix.sh "$@"

ANSIBLE_REMOTE_TMP="/tmp" ANSIBLE_REMOTE_USER="1000" ./posix.sh "$@"
ANSIBLE_PODMAN_EXECUTABLE=fakepodman ./posix.sh "$@" 2>&1 | grep "fakepodman command not found in PATH"

ANSIBLE_PODMAN_EXECUTABLE=fakepodman ./posix.sh "$@" && {
    echo "Playbook with fakepodman should fail!"
    exit 1
}
ANSIBLE_VERBOSITY=4 ANSIBLE_PODMAN_EXTRA_ARGS=" --log-level debug " ./posix.sh "$@" | grep "level=debug msg="
