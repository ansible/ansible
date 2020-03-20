#!/usr/bin/env bash

set -ux
export ANSIBLE_BECOME_ALLOW_SAME_USER=1
ansible-playbook -i ../../inventory playbook.yml -e "output_dir=${OUTPUT_DIR}" -v "$@"
