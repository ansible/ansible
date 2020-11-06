#!/usr/bin/env bash

set -eux
export ANSIBLE_ROLES_PATH=../
ansible-playbook -i ../../inventory runme.yml -e "output_dir=${OUTPUT_DIR}" -v "$@"
