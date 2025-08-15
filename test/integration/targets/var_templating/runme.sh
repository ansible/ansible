#!/usr/bin/env bash

set -eux

# this should succeed since we override the undefined variable
ansible-playbook undefined.yml -i inventory -v "$@" -e '{"override_value": "overridden by -e"}'

# this should work since we dont use the variable
ansible-playbook undall.yml -i inventory -v "$@"

# test hostvars templating
ansible-playbook task_vars_templating.yml -v "$@"

# there should be an attempt to use 'sudo' in the connection debug output
ANSIBLE_BECOME_ALLOW_SAME_USER=true ansible-playbook test_connection_vars.yml -vvvv "$@" | tee /dev/stderr | grep 'sudo \-H \-S'

# test vars deprecation
[ $(ansible -m debug  -a "msg='{{vars}}'" localhost 2>&1 | grep -c 'The internal "vars" dictionary is deprecated') = 1 ]
[ $(ansible -m debug  -a 'msg="{{vars["'"ansible_python_interpreter"'"]}}"' localhost 2>&1 | grep -c 'The internal "vars" dictionary is deprecated') | = 1]
