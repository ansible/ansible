#!/usr/bin/env bash

set -eux

# this should succeed since we override the undefined variable
ansible-playbook undefined.yml -i inventory -v "$@" -e '{"mytest": False}'

# this should still work, just show that var is undefined in debug
ansible-playbook undefined.yml -i inventory -v "$@"

# this should work since we dont use the variable
ansible-playbook undall.yml -i inventory -v "$@"

# test hostvars templating
ansible-playbook task_vars_templating.yml -v "$@"

ansible-playbook test_connection_vars.yml -v "$@" 2>&1 | grep 'sudo'
