#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -e

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

# This is needed for the ubuntu1604py3 tests
# Ubuntu patches virtualenv to make the default python2
# but for the python3 tests we need virtualenv to use python3
if [ -f /usr/bin/python3 ]
then
    PYTHON="--python /usr/bin/python3"
else
    PYTHON=""
fi

virtualenv --system-site-packages $PYTHON "${MYTMPDIR}/jinja2"

source "${MYTMPDIR}/jinja2/bin/activate"

echo "################"
echo "Python path: $(which python)"
echo "Python version: $(python -V)"
echo "################"

pip install -U jinja2==2.9.4

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"

pip install -U "jinja2<2.9.0"

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"

deactivate

rm -r "${MYTMPDIR}"
