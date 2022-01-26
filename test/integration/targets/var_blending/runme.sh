#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../
ansible-playbook test_var_blending.yml -i inventory -e @test_vars.yml -v "$@"
