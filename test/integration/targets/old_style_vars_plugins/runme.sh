#!/usr/bin/env bash

set -eux

export ANSIBLE_VARS_PLUGINS=./vars_plugins

# Test vars plugin without REQUIRES_ENABLED class attr and vars plugin with REQUIRES_ENABLED = False run by default
[ "$(ansible-inventory -i localhost, --list --yaml all "$@" | grep -Ec '(implicitly|explicitly)_auto_enabled')" = "2" ]

# Test vars plugin with REQUIRES_ENABLED=True only runs when enabled
[ "$(ansible-inventory -i localhost, --list --yaml all "$@" | grep -Ec 'require_enabled')" = "0" ]
export ANSIBLE_VARS_ENABLED=require_enabled
[ "$(ansible-inventory -i localhost, --list --yaml all "$@" | grep -c 'require_enabled')" = "1" ]

# Test the deprecated class attribute
export ANSIBLE_VARS_PLUGINS=./deprecation_warning
WARNING="The VarsModule class variable 'REQUIRES_WHITELIST' is deprecated. Use 'REQUIRES_ENABLED' instead."
ANSIBLE_DEPRECATION_WARNINGS=True ANSIBLE_NOCOLOR=True ANSIBLE_FORCE_COLOR=False \
	ansible-inventory -i localhost, --list all 2> err.txt
ansible localhost -m debug -a "msg={{ lookup('file', 'err.txt') | regex_replace('\n', '') }}" | grep "$WARNING"

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

verbose_result="$(ANSIBLE_DEBUG=True ansible-playbook test_task_vars.yml)"
test "$(grep -c "Loading VarsModule 'host_group_vars'" <<< "$verbose_result")" == 1
test "$(grep -c "Loading VarsModule 'require_enabled'" <<< "$verbose_result")" -gt 50
test "$(grep -c "Loading VarsModule 'auto_enabled'" <<< "$verbose_result")" -gt 50

export ANSIBLE_VARS_ENABLED=ansible.builtin.host_group_vars
verbose_result="$(ANSIBLE_DEBUG=True ansible-playbook test_task_vars.yml)"
test "$(grep -c "Loading VarsModule 'host_group_vars'" <<< "$verbose_result")" == 1
test "$(grep -c "Loading VarsModule 'require_enabled'" <<< "$verbose_result")" == 1
test "$(grep -c "Loading VarsModule 'auto_enabled'" <<< "$verbose_result")" -gt 50
