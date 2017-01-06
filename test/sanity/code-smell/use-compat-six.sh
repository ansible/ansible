#!/bin/sh

# Do we want to check dynamic inventory, bin, etc?
BASEDIR=${1-"lib"}
# REGEX of individual files where the import of six is not a problem
# digital_ocean is checking for six because dopy doesn't specify the
#   requirement on six so it needs to try importing six to give the correct error
#   message
WHITELIST='(lib/ansible/modules/cloud/digital_ocean/digital_ocean.py)'

SIX_USERS=$(find "$BASEDIR" -name '*.py' -exec grep -wH six '{}' '+' \
    | grep import \
    | grep -v ansible.compat \
    | grep -v ansible.module_utils.six \
    | egrep -v "^$WHITELIST:"
)

if [ "${SIX_USERS}" ]; then
    echo "${SIX_USERS}"
    exit 1
fi
