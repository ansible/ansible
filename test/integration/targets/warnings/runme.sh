#!/usr/bin/env bash

set -o nounset -o errexit -o xtrace

# should have warning on localhost
[ "$(ansible localhost -m debug 2>&1 |grep -wc 'WARNING')" -eq "1" ]

# should have warning on interpreter
[ "$(ansible testhost -m ping -i testhost, -c local 2>&1 |grep -wc 'WARNING')" -eq "1" ]

# should have no warnings
[ "$(ansible testhost -m ping -i testhost, -c local -e ansible_python_interpreter='{{ansible_playbook_python}}' 2>&1 |grep -wc 'WARNING')" -eq "0" ]
