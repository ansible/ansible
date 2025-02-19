#!/usr/bin/env bash

source ../collection/setup.sh

set -eux
export ANSIBLE_DEPRECATION_WARNINGS=1
export ANSIBLE_COLLECTIONS_PATH="${WORK_DIR}"
export ANSIBLE_STRATEGY=ns.col.external
output="$(ansible localhost -m debug 2>&1 | tee -a /dev/stderr)"
if [[ "${output}" != *"Use of strategy plugins not included in ansible.builtin"* ]]; then
    echo 'ERROR: Did not find deprecation warning for removal of strategy plugins'
    exit 1
fi
