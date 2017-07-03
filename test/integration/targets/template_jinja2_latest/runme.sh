#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -ex

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

trap 'rm -rf "${MYTMPDIR}"' EXIT

# This is needed for the ubuntu1604py3 tests
# Ubuntu patches virtualenv to make the default python2
# but for the python3 tests we need virtualenv to use python3
PYTHON=$("python${ANSIBLE_TEST_PYTHON_VERSION:-}" -c "import sys; print(sys.executable)")

virtualenv --system-site-packages --python "${PYTHON}" "${MYTMPDIR}/jinja2"

source "${MYTMPDIR}/jinja2/bin/activate"

pip install -U jinja2

ansible-playbook -i ../../inventory main.yml -e @../../integration_config.yml -v "$@"
