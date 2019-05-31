#!/usr/bin/env bash

set -eux

export ANSIBLE_STDOUT_CALLBACK=yaml

ansible-playbook -i inventory/hosts.yml main.yml  "$@"
