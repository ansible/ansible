#!/usr/bin/env bash

set -ux

set -e

## sftp
#./posix.sh "$@"
## scp
#ANSIBLE_SCP_IF_SSH=true ./posix.sh "$@" "${scp_args[@]}"
## piped
#ANSIBLE_SSH_TRANSFER_METHOD=piped ./posix.sh "$@"

echo 'made it here'

exit 1
