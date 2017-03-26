#!/usr/bin/env bash

set -eux

# sftp
./posix.sh "$@"
# scp
ANSIBLE_SCP_IF_SSH=true ./posix.sh "$@"
# piped
ANSIBLE_SSH_TRANSFER_METHOD=piped ./posix.sh "$@"
