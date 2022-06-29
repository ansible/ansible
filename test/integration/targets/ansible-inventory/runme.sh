#!/usr/bin/env bash

source virtualenv.sh
export ANSIBLE_ROLES_PATH=../
set -euvx

ansible-playbook test.yml "$@"
