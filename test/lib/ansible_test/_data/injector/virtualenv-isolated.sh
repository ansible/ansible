#!/usr/bin/env bash
# Create and activate a fresh virtual environment with `source virtualenv-isolated.sh`.

rm -rf "${OUTPUT_DIR}/venv"

# Try to use 'venv' if it is available, then fallback to 'virtualenv' since some systems provide 'venv' although it is non-functional.
if [[ "${ANSIBLE_TEST_PYTHON_VERSION}" =~ ^2\. ]] || ! "${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m venv "${OUTPUT_DIR}/venv" > /dev/null 2>&1; then
    rm -rf "${OUTPUT_DIR}/venv"
    "${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m virtualenv --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${OUTPUT_DIR}/venv"
fi

set +ux
source "${OUTPUT_DIR}/venv/bin/activate"
set -ux

if [[ "${ANSIBLE_TEST_COVERAGE}" ]]; then
    pip install coverage -c ../../../runner/requirements/constraints.txt --disable-pip-version-check
fi
