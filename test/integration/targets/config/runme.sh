#!/usr/bin/env bash

set -eux

# ignore empty env var and use default
# shellcheck disable=SC1007
ANSIBLE_TIMEOUT= ansible -m ping testhost -i ../../inventory "$@"

# env var is wrong type, this should be a fatal error pointing at the setting
ANSIBLE_TIMEOUT='lola' ansible -m ping testhost -i ../../inventory "$@" 2>&1|grep 'Invalid type for configuration option setting: DEFAULT_TIMEOUT'
