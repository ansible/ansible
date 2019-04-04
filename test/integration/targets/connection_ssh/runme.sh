#!/usr/bin/env bash

set -eux

# temporary work-around for issues due to new scp filename checking
# https://github.com/ansible/ansible/issues/52640
if [[ "$(scp -T 2>&1)" == "usage: scp "* ]]; then
    # scp supports the -T option
    # work-around required
    scp_args=("-e" "ansible_scp_extra_args=-T")
else
    # scp does not support the -T option
    # no work-around required
    # however we need to put something in the array to keep older versions of bash happy
    scp_args=("-e" "")
fi

# sftp
./posix.sh "$@"
# scp
ANSIBLE_SCP_IF_SSH=true ./posix.sh "$@" "${scp_args[@]}"
# piped
ANSIBLE_SSH_TRANSFER_METHOD=piped ./posix.sh "$@"
