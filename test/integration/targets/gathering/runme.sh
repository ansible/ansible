#!/usr/bin/env bash

set -eux

ANSIBLE_GATHERING=smart ansible-playbook smart.yml --flush-cache -i ../../inventory -v "$@"
ANSIBLE_GATHERING=implicit ansible-playbook implicit.yml --flush-cache -i ../../inventory -v "$@"
ANSIBLE_GATHERING=explicit ansible-playbook explicit.yml --flush-cache -i ../../inventory -v "$@"
