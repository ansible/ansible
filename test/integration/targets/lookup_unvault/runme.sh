#!/usr/bin/env bash

set -eux

# run tests
ansible-playbook unvault.yml --vault-password-file='secret' -v "$@"
