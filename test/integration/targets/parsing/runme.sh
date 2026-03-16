#!/usr/bin/env bash

set -eux

ansible-playbook parsing.yml -i ../../inventory "$@" -e "output_dir=${OUTPUT_DIR}"
ansible-playbook good_parsing.yml -i ../../inventory "$@"
