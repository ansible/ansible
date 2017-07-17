#!/usr/bin/env bash

set -eux

OUTPUT_DIR=/tmp/ansible-test
mkdir -p $OUTPUT_DIR
ansible-playbook playbook.yml -i inventory \
    -e output_dir="${OUTPUT_DIR}" \
    -e non_local="yes" \
    "$@"
