#!/usr/bin/env bash

set -eux

ansible-playbook test_var_blending.yml -i inventory -e @test_vars.yml -v "$@"

ansible-playbook extra_not_in_hostvars.yml -i inventory -e 'only_extra=from_extra_vars, myhostvar=from_extra_vars' -v "$@"
