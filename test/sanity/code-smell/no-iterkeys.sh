#!/bin/sh

ITERKEYS_USERS=$(grep -r iterkeys . \
    --exclude-dir .git \
    --exclude-dir .tox \
    --exclude-dir docsite \
    | grep -v \
    -e lib/ansible/compat/six/_six.py \
    -e lib/ansible/module_utils/six.py \
    -e no-iterkeys.sh \
    -e '^[^:]*:#'
    )

if [ "${ITERKEYS_USERS}" ]; then
    echo "${ITERKEYS_USERS}"
    exit 1
fi
