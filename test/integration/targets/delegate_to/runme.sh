#!/usr/bin/env bash

set -eux

ANSIBLE_SSH_ARGS='-C -o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null' \
    ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook test_delegate_to.yml -i ../../inventory -v "$@"
