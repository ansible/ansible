#!/usr/bin/env bash

set -eux

pip install pypsrp
cd ../connection

INVENTORY=../../inventory.winrm ./test.sh \
    -e target_hosts=winrm \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    -e ansible_psrp_cert_validation=False \
    -c psrp \
    "$@"
