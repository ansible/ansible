#!/usr/bin/env bash

set -eux

ansible-playbook test_var_blending.yml -i inventory -e @test_vars.yml -v "$@"
