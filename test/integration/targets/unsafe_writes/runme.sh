#!/usr/bin/env bash

set -eux

# test w/o fallback env var
ansible-playbook basic.yml -i ../../inventory "$@"

# test enabled fallback env var
ANSIBLE_UNSAFE_WRITES=1 ansible-playbook basic.yml -i ../../inventory "$@"

# test disabled fallback env var
ANSIBLE_UNSAFE_WRITES=0 ansible-playbook basic.yml -i ../../inventory "$@"
