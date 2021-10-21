#!/usr/bin/env bash
set -eux

export ANSIBLE_COLLECTIONS_PATH=.
ansible-playbook test_turbo_mode.yaml -vvv
ansible-playbook test_turbo_fail.yaml -vvv 
