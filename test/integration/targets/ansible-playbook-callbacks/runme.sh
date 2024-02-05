#!/usr/bin/env bash

set -eux

export ANSIBLE_CALLBACK_PLUGINS=../support-callback_plugins/callback_plugins
export ANSIBLE_ROLES_PATH=../
export ANSIBLE_STDOUT_CALLBACK=callback_debug

ANSIBLE_HOST_PATTERN_MISMATCH=warning ansible-playbook all-callbacks.yml 2>/dev/null | sort | uniq -c | tee callbacks_list.out
diff -w callbacks_list.out callbacks_list.expected

for strategy in linear free; do
  ANSIBLE_STRATEGY=$strategy ansible-playbook include_role-fail.yml 2>/dev/null | sort | uniq -c | tee callback_list_include_role_fail.out
  diff -w callback_list_include_role_fail.out callback_list_include_role_fail.expected
done
