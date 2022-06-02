#!/usr/bin/env bash

set -eux

ansible-playbook -i inventory.yml refresh.yml "$@"
ansible-playbook -i inventory.yml refresh_preserve_dynamic.yml "$@"
