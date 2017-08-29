#!/bin/sh

BASESTRING_USERS=$(grep -r basestring . \
    --exclude-dir .git \
    --exclude-dir .tox \
    | grep isinstance \
    | grep -v \
    -e test/results/ \
    -e docs/docsite/_build/ \
    -e docs/docsite/rst/dev_guide/testing/sanity/ \
    -e lib/ansible/module_utils/six/__init__.py \
    -e '^[^:]*:#'
    )

if [ "${BASESTRING_USERS}" ]; then
    echo "${BASESTRING_USERS}"
    exit 1
fi
