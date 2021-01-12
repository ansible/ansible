#!/usr/bin/env bash

set -eux

ansible-playbook basic.yml -i ../../inventory -e "output_dir=${OUTPUT_DIR}" "$@"
