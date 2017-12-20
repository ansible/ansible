#!/bin/sh

UNICODE_LITERALS_USERS=$(grep -r unicode_literals . \
    --exclude-dir .git \
    --exclude-dir .tox \
    --exclude no-unicode-literals.sh \
    --exclude no-unicode-literals.rst |
    grep -v ./test/results | \
    grep -v ansible.egg-info/SOURCES.txt \
    )

if [ "${UNICODE_LITERALS_USERS}" ]; then
    echo "${UNICODE_LITERALS_USERS}"
    exit 1
fi

exit 0
