#!/bin/sh

ITERITEMS_USERS=$(grep -rI '\.iteritems' . \
    --exclude-dir .git \
    --exclude-dir .tox \
    --exclude-dir docsite \
    | grep -v \
    -e 'six\.iteritems' \
    -e lib/ansible/module_utils/six/__init__.py \
    -e test/sanity/code-smell/no-dict-iteritems.sh \
    )

if [ "${ITERITEMS_USERS}" ]; then
    echo 'iteritems has been removed in python3.  Alternatives:'
    echo '    for KEY, VALUE in DICT.items():'
    echo '    from ansible.module_utils.six import iteritems ; for KEY, VALUE in iteritems(DICT):'
    echo "${ITERITEMS_USERS}"
    exit 1
fi
