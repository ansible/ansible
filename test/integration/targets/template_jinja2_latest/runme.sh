#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -ex

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

trap 'rm -rf "${MYTMPDIR}"' EXIT

virtualenv --system-site-packages --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${MYTMPDIR}/jinja2"

source "${MYTMPDIR}/jinja2/bin/activate"

pip install -U jinja2

ANSIBLE_ROLES_PATH=../
export ANSIBLE_ROLES_PATH

ansible-playbook -i ../../inventory main.yml -e @../../integration_config.yml -v "$@"
