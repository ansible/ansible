#!/bin/sh

constraints=$(
    grep '.' test/runner/requirements/*.txt \
        | grep -v '(sanity_ok)$' \
        | sed 's/ *;.*$//; s/ #.*$//' \
        | grep -v '/constraints.txt:' \
        | grep '[<>=]'
)

if [ "${constraints}" ]; then
    echo 'Constraints for test requirements should be in "test/runner/requirements/constraints.txt".'
    echo 'The following constraints were found outside the "constraints.txt" file:'
    echo "${constraints}"
    exit 1
fi
