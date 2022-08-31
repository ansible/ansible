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
