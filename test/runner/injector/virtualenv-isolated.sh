#!/usr/bin/env bash
# Create and activate a fresh virtual environment with `source virtualenv-isolated.sh`.

rm -rf "${OUTPUT_DIR}/venv"
"${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m virtualenv --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${OUTPUT_DIR}/venv"
set +ux
source "${OUTPUT_DIR}/venv/bin/activate"
set -ux

if [[ "${ANSIBLE_TEST_COVERAGE}" ]]; then
    pip install coverage -c ../../../runner/requirements/constraints.txt --disable-pip-version-check
fi
