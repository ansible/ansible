#!/usr/bin/env bash

set -e

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

if [ -f /usr/bin/python3 ]
then
    PYTHON="--python /usr/bin/python3"
else
    PYTHON=""
fi

virtualenv --system-site-packages $PYTHON "${MYTMPDIR}/jinja2"

source "${MYTMPDIR}/jinja2/bin/activate"

pip install -U jinja2==2.9.4

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v

pip install -U "jinja2<2.9.0"

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v

deactivate

rm -r "${MYTMPDIR}"
