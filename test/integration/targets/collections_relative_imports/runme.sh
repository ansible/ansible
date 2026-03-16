#!/usr/bin/env bash

set -eux

# we need multiple plays, and conditional import_playbook is noisy and causes problems, so choose here which one to use...
if [[ ${INVENTORY_PATH} == *.winrm ]]; then
  export TEST_PLAYBOOK=windows.yml
else
  export TEST_PLAYBOOK=test.yml

fi

ANSIBLE_COLLECTIONS_PATH="${PWD}/collection_root" ansible-playbook "${TEST_PLAYBOOK}" -i "${INVENTORY_PATH}" "$@"
