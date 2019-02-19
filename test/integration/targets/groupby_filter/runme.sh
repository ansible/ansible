#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -ex

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

trap 'rm -rf "${MYTMPDIR}"' EXIT

virtualenv --system-site-packages --python "${ANSIBLE_TEST_PYTHON_INTERPRETER}" "${MYTMPDIR}/jinja2"

source "${MYTMPDIR}/jinja2/bin/activate"

pip install -U jinja2==2.9.4

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"

pip install -U "jinja2<2.9.0"

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"
