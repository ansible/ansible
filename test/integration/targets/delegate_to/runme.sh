#!/usr/bin/env bash

set -eux

ANSIBLE_SSH_ARGS='-C -o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null' \
    ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook test_delegate_to.yml -i inventory -v "$@"

ansible-playbook test_loop_control.yml -v "$@"

ansible-playbook test_delegate_to_loop_randomness.yml -v "$@"

ansible-playbook delegate_and_nolog.yml -i inventory -v "$@"

ansible-playbook test_delegate_to_loop_caching.yml -i inventory -v "$@"

ansible-playbook delegate_facts_block.yml -i inventory -v "$@"
