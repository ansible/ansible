#!/usr/bin/env bash

set -eux

export ANSIBLE_VARS_PLUGINS=./vars_plugins

# Test vars plugin without REQUIRES_ENABLED class attr and vars plugin with REQUIRES_ENABLED = False run by default
[ "$(ansible-inventory -i localhost, --list --yaml all "$@" | grep -Ec '(implicitly|explicitly)_auto_enabled')" = "2" ]

# Test vars plugin with REQUIRES_ENABLED=True only runs when enabled
[ "$(ansible-inventory -i localhost, --list --yaml all "$@" | grep -Ec 'require_enabled')" = "0" ]
export ANSIBLE_VARS_ENABLED=require_enabled
[ "$(ansible-inventory -i localhost, --list --yaml all "$@" | grep -c 'require_enabled')" = "1" ]

# Test how many times vars plugins are loaded for a simple play containing a task
# host_group_vars is stateless, so we can load it once and reuse it, every other vars plugin should be instantiated before it runs
cat << EOF > "test_task_vars.yml"
---
- hosts: localhost
  connection: local
  gather_facts: no
  tasks:
  - debug:
EOF

# hide the debug noise by dumping to a file
trap 'rm -rf -- "out.txt"' EXIT

ANSIBLE_DEBUG=True ansible-playbook test_task_vars.yml > out.txt
[ "$(grep -c "Loading VarsModule 'host_group_vars'" out.txt)" -eq 1 ]
[ "$(grep -c "Loading VarsModule 'require_enabled'" out.txt)" -eq 22 ]
[ "$(grep -c "Loading VarsModule 'auto_enabled'" out.txt)" -eq 22 ]

export ANSIBLE_VARS_ENABLED=ansible.builtin.host_group_vars
ANSIBLE_DEBUG=True ansible-playbook test_task_vars.yml > out.txt
[ "$(grep -c "Loading VarsModule 'host_group_vars'" out.txt)" -eq 1 ]
[ "$(grep -c "Loading VarsModule 'require_enabled'" out.txt)" -lt 3 ]
[ "$(grep -c "Loading VarsModule 'auto_enabled'" out.txt)" -eq 22 ]

ansible localhost -m include_role -a 'name=a' "$@"
