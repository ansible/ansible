#!/usr/bin/env bash

set -eux

# run type tests
ansible-playbook -i ../../inventory types.yml -v "$@"

# test timeout
ansible-playbook -i ../../inventory timeout.yml -v "$@"
