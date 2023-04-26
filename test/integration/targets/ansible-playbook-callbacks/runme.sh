#!/usr/bin/env bash

set -eux

export ANSIBLE_CALLBACK_PLUGINS=../support-callback_plugins/callback_plugins
export ANSIBLE_ROLES_PATH=../
export ANSIBLE_STDOUT_CALLBACK=callback_debug

ansible-playbook all-callbacks.yml 2>/dev/null | sort | uniq -c | tee callbacks_list.out

diff -w callbacks_list.out callbacks_list.expected
