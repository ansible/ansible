#!/usr/bin/env bash

set -eux -o pipefail

# the callback itself will raise AssertionError and fail if called > 1x
_ASSERT_OOPS=1 ANSIBLE_STDOUT_CALLBACK=oops_always_enabled ansible-playbook one-task.yml > no_double_callbacks.txt 2>&1

grep 'no double callbacks test PASS' no_double_callbacks.txt

if ANSIBLE_FORCE_COLOR=0 ANSIBLE_STDOUT_CALLBACK=missing_base_class ansible-playbook one-task.yml > missing_base_class.txt 2>&1; then false; else true; fi

grep "due to missing base class 'CallbackBase'" missing_base_class.txt

# the callback itself will raise AssertionError and fail if some callback methods do not execute
ANSIBLE_STDOUT_CALLBACK=legacy_warning_display ansible-playbook test_legacy_warning_display.yml "${@}" 2>&1 | tee legacy_warning_out.txt

grep 'legacy warning display callback test PASS' legacy_warning_out.txt

# the callback itself will raise AssertionError and fail if some callback methods do not execute
ANSIBLE_STDOUT_CALLBACK=v1_only_methods ansible-playbook test_v1_methods.yml "${@}" | tee v1_methods_out.txt

grep 'v1 callback test PASS' v1_methods_out.txt
