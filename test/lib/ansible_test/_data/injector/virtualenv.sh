#!/usr/bin/env bash
# Create and activate a fresh virtual environment with `source virtualenv.sh`.

rm -rf "${OUTPUT_DIR}/venv"

# Try to use 'venv' if it is available, then fallback to 'virtualenv' since some systems provide 'venv' although it is non-functional.
if [ -z "${ANSIBLE_TEST_PREFER_VENV:-}" ] || [[ "${ANSIBLE_TEST_PYTHON_VERSION}" =~ ^2\. ]] || ! "${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m venv --system-site-packages "${OUTPUT_DIR}/venv" > /dev/null 2>&1; then
    rm -rf "${OUTPUT_DIR}/venv"
    "${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m virtualenv --system-site-packages --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${OUTPUT_DIR}/venv"
fi

set +ux
source "${OUTPUT_DIR}/venv/bin/activate"
set -ux
