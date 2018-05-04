#!/usr/bin/env bash

set -eux

export ANSIBLE_HOSTS=../../inventory

trap 'rm -f test_callback.log *.retry' EXIT

ansible-playbook include_tasks_success.yml
diff include_tasks_success.log test_callback.log

ansible-playbook include_success.yml
diff include_success.log test_callback.log

ansible-playbook include_dynamic_success.yml
diff include_dynamic_success.log test_callback.log

# shellcheck disable=SC2015
ansible-playbook include_tasks_failure.yml && exit 1 || true
diff include_tasks_failure.log test_callback.log

# shellcheck disable=SC2015
ansible-playbook include_failure.yml && exit 1 || true
diff include_failure.log test_callback.log

# shellcheck disable=SC2015
ansible-playbook include_dynamic_failure.yml && exit 1 || true
diff include_dynamic_failure.log test_callback.log
