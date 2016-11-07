#!/bin/sh

found=''

for path in lib/ansible/modules/ test/units/; do
    files=$(find "${path}" -name __init__.py -size '+0')

    if [ "${files}" ]; then
        echo "${files}"
        found=1
    fi
done

if [ "${found}" ]; then
    echo "One or more __init__.py file(s) listed above are non-empty."
    exit 1
fi
