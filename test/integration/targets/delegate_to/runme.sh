#!/usr/bin/env bash

set -eux

ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook test_delegate_to.yml -i ../../inventory -v "$@"
