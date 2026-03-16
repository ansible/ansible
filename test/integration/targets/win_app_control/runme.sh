#!/usr/bin/env bash

if ! command -V pwsh; then
  echo "skipping test since pwsh is not available"
  exit 0
fi

source ../collection/setup.sh

set -x

ANSIBLE_DIR="$( python -c "import pathlib, ansible; print(pathlib.Path(ansible.__file__).parent)" )"

ANSIBLE_COLLECTIONS_PATH="${WORK_DIR}" ANSIBLE_DISPLAY_TRACEBACK=error \
    ansible-playbook "${TEST_DIR}/main.yml" \
    --inventory "${TEST_DIR}/../../inventory.winrm" \
    --extra-vars "local_tmp_dir=${WORK_DIR} ansible_install_dir=${ANSIBLE_DIR}" \
    "${@}"
