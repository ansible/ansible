#!/usr/bin/env bash

set -ux
export ANSIBLE_BECOME_ALLOW_SAME_USER=1
export ANSIBLE_ROLES_PATH=../
ansible-playbook -i ../../inventory runme.yml -e "output_dir=${OUTPUT_DIR}" -v "$@"
