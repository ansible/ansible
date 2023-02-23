#!/usr/bin/env bash

if [[ "${ANSIBLE_DEBUG}" == true ]]  # `ansible-test` invoked with `--debug`
then
    PYTEST_VERY_VERBOSE_FLAG=-vvvvv
    SET_DEBUG_MODE=-x
else
    ANSIBLE_DEBUG=false
    PYTEST_VERY_VERBOSE_FLAG=
    SET_DEBUG_MODE=+x
fi


set -eEuo pipefail

source virtualenv.sh

set "${SET_DEBUG_MODE}"

export PIP_DISABLE_PIP_VERSION_CHECK=true
export PIP_NO_PYTHON_VERSION_WARNING=true
export PIP_NO_WARN_SCRIPT_LOCATION=true

python -Im pip install 'pytest ~= 7.2.0'
python -Im pytest ${PYTEST_VERY_VERBOSE_FLAG} \
  --basetemp="${OUTPUT_DIR}/pytest-tmp" \
  --color=yes \
  --showlocals \
  -p no:forked \
  -p no:mock \
  -ra
