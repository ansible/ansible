#!/usr/bin/env bash

set -eux

PLAYBOOK_DIR="${PWD}"

source ../collection/setup.sh

EXT=$( python -c 'import importlib.machinery as i; print(next(iter([s for s in i.all_suffixes() if s != ".py"])))' )
touch "temp_pythonpath/my_module/sub/foo${EXT}"

ANSIBLE_COLLECTIONS_PATH="${PWD}../../../" \
    ANSIBLE_LOCALHOST_WARNING=false \
    PYTHONPATH="./temp_pythonpath:${PYTHONPATH}" \
    ansible-playbook "${PLAYBOOK_DIR}/main.yml" "$@"
