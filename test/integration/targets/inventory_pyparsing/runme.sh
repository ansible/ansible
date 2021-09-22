#!/usr/bin/env bash

set -eux

# https://github.com/ansible/ansible/pull/75645

ver=$(python -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/') || ver=-1
HAS_PYPARSING=$(python -c 'import sys; sys.tracebacklimit = 0; import pyparsing; print(0)') || HAS_PYPARSING=-1
if [ "$ver" -lt "28" ] || [ ! "$HAS_PYPARSING" -eq 0  ]; then
    echo "Skipping inventory_pyparsing test. Requires python 2.8 or greater and successful pyparsing import."
    exit 0
fi


trap 'echo "Pyparsing pattern test failed"' ERR
ansible-playbook -i inventory test_limit_pyparsing.yml "$@"
ansible-playbook -i inventory test_lookup_pyparsing.yml "$@"

