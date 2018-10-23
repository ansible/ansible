#!/usr/bin/env bash

set -eux

python.py -m pip install pypsrp
cd ../connection

INVENTORY=../../inventory.winrm ./test.sh \
    -i ../connection_psrp/inventory.ini \
    -e target_hosts=winrm \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "$@"

cd ../connection_psrp

ansible-playbook -i ../../inventory.winrm -i inventory.ini tests.yml \
    "$@"
