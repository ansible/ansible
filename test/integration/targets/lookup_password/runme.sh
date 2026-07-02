#!/usr/bin/env bash

set -eux

source virtualenv.sh

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml -e "output_dir=${OUTPUT_DIR}" "$@"
