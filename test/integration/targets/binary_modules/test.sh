#!/usr/bin/env bash

set -eux

[ -f "${INVENTORY}" ]

ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook download_binary_modules.yml -i "${INVENTORY}" -v "$@"
ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook test_binary_modules.yml     -i "${INVENTORY}" -v "$@"
