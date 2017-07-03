#!/usr/bin/env bash

set -eux

ANSIBLE_TEST_REMOTE_INTERPRETER='' ./posix.sh "$@"

ANSIBLE_TEST_REMOTE_INTERPRETER='' ANSIBLE_REMOTE_USER="1000" ./posix.sh "$@"
