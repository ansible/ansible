#!/usr/bin/env bash

set -eux

# simple run
ansible-playbook --vault-password-file password main.yml
