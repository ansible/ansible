#!/usr/bin/env bash

set -eux

# ignore empty env var and use default
# shellcheck disable=SC1007
ANSIBLE_TIMEOUT= ansible -m ping testhost -i ../../inventory "$@"

# env var is wrong type, this should be a fatal error pointing at the setting
ANSIBLE_TIMEOUT='lola' ansible -m ping testhost -i ../../inventory "$@" 2>&1|grep 'Invalid type for configuration option setting: DEFAULT_TIMEOUT'

# https://github.com/ansible/ansible/issues/69577
ANSIBLE_REMOTE_TMP="$HOME/.ansible/directory_with_no_space"  ansible -m ping testhost -i ../../inventory "$@"

ANSIBLE_REMOTE_TMP="$HOME/.ansible/directory with space"  ansible -m ping testhost -i ../../inventory "$@"

ANSIBLE_CONFIG=nonexistent.cfg ansible-config dump --only-changed -v | grep 'No config file found; using defaults'

# https://github.com/ansible/ansible/pull/73715
ANSIBLE_CONFIG=inline_comment_ansible.cfg ansible-config dump --only-changed | grep "'ansibull'"
