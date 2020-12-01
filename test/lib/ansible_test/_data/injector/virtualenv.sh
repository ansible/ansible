#!/usr/bin/env bash
# Create and activate a fresh virtual environment with `source virtualenv.sh`.

# Privilege venv if it is available but fallback to virtualenv
# https://github.com/ansible/ansible/issues/72738
"${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m venv &> /dev/null
if [ $? -eq 2 ]; then
    module="venv"
else
    module="virtualenv"
fi

rm -rf "${OUTPUT_DIR}/venv"
"${ANSIBLE_TEST_PYTHON_INTERPRETER}" -m $module --system-site-packages --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${OUTPUT_DIR}/venv"
set +ux
source "${OUTPUT_DIR}/venv/bin/activate"
set -ux
