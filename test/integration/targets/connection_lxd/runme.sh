#!/usr/bin/env bash

set -eux

ANSIBLE_TEST_REMOTE_INTERPRETER='' ./posix.sh "$@"
