#!/usr/bin/env bash

set -eux

./posix.sh "$@"

ANSIBLE_REMOTE_TMP="/tmp" ANSIBLE_REMOTE_USER="1000" ./posix.sh "$@"
