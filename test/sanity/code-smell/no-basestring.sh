#!/bin/sh

BASESTRING_USERS=$(grep -r basestring . \
    --exclude-dir .git \
    --exclude-dir .tox \
    | grep isinstance \
    | grep -v \
    -e test/results/ \
    -e lib/ansible/compat/six/_six.py \
    -e lib/ansible/module_utils/six.py \
    -e lib/ansible/modules/ \
    -e '^[^:]*:#'
    )

if [ "${BASESTRING_USERS}" ]; then
    echo "${BASESTRING_USERS}"
    exit 1
fi
