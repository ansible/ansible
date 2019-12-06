#!/usr/bin/env bash

set -ux

ansible-playbook -i ../../inventory playbook.yml -e "output_dir=${OUTPUT_DIR}" -v "$@"
