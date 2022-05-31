#!/usr/bin/env bash

set -eux

source virtualenv.sh

ANSIBLE_ROLES_PATH=../ ansible-playbook test.yml -i inventory "$@"
