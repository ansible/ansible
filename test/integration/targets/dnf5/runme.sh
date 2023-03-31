#!/usr/bin/env bash

set -ux
export ANSIBLE_ROLES_PATH=../
ansible-playbook playbook.yml "$@"
