#!/usr/bin/env bash

set -o pipefail

export ANSIBLE_STDOUT_CALLBACK=callback_host_count

# the number of forks matter, see callback_plugins/callback_host_count.py
ansible-playbook --inventory hosts --forks 2 playbook.yml | tee "${OUTPUT_DIR}/out.txt"

[ "$(grep -c 'host_pinned_test_failed' "${OUTPUT_DIR}/out.txt")" -eq 0 ]
