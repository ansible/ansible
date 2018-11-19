#!/usr/bin/env bash

set -eux

# ignore empty env var and use default
# shellcheck disable=SC1007
ANSIBLE_TIMEOUT= ansible -m ping localhost "$@"

# env var is wrong type, this should be a fatal error pointing at the setting
ANSIBLE_TIMEOUT='lola' ansible -m ping localhost "$@" 2>&1|grep 'AnsibleOptionsError: Invalid type for configuration option DEFAULT_TIMEOUT'
