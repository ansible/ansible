#!/bin/sh

ITERKEYS_USERS=$(grep -r -I iterkeys . \
    --exclude-dir .git \
    --exclude-dir .tox \
    --exclude-dir .idea \
    --exclude-dir docsite \
    --exclude-dir results \
    | grep -v \
    -e lib/ansible/compat/six/_six.py \
    -e lib/ansible/module_utils/six.py \
    -e test/sanity/code-smell/no-iterkeys.sh \
    -e '^[^:]*:#'
    )

if [ "${ITERKEYS_USERS}" ]; then
    echo 'iterkeys has been removed in python3.  Use "for KEY in DICT:" instead'
    echo "${ITERKEYS_USERS}"
    exit 1
fi
