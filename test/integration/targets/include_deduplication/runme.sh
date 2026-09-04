#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../

ansible-playbook -i hosts runme.yml "$@"
