#!/usr/bin/env bash

set -eux

cd ../connection

INVENTORY=../../inventory.winrm ./test.sh \
    -e hosts=winrm \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "$@"
