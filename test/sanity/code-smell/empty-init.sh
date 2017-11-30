#!/bin/sh

found=''

for path in lib/ansible/modules/ lib/ansible/module_utils test/units/; do
    # facts is grandfathered in but will break namespacing.  Only way to fix it
    # is to deprecate and eventually remove.
    # six will break namespacing but because it is bundled we should not be overriding it
    files=$(find "${path}" -name __init__.py -size '+0' | sed '\!lib/ansible/module_utils/\(six\|facts\)/__init__.py!d')

    if [ "${files}" ]; then
        echo "${files}"
        found=1
    fi
done

if [ "${found}" ]; then
    echo "One or more __init__.py file(s) listed above are non-empty."
    exit 1
fi
