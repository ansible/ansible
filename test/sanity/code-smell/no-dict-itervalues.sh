#!/bin/sh

ITERVALUES_USERS=$(grep -rI '\.itervalues' . \
    --exclude-dir .git \
    --exclude-dir .tox \
    --exclude-dir docsite \
    | grep -v \
    -e 'six\.itervalues' \
    -e lib/ansible/module_utils/six/__init__.py \
    -e test/sanity/code-smell/no-dict-itervalues.sh \
    )

if [ "${ITERVALUES_USERS}" ]; then
    echo 'itervalues has been removed in python3.  Alternatives:'
    echo '    for VALUE in DICT.values():'
    echo '    from ansible.module_utils.six import itervalues ; for VALUE in itervalues(DICT):'
    echo "${ITERVALUES_USERS}"
    exit 1
fi
