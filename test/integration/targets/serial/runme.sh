#!/usr/bin/env bash

set -eux

ansible-playbook -i inventory.yml "$@" unreachable_serial.yml | tee out.txt
[ "$(grep -c 'SHOULD NOT HAPPEN' out.txt)" -eq 0 ]
[ "$(grep -c 'failed=1' out.txt)" -eq 1 ]
[ "$(grep -c 'unreachable=1' out.txt)" -eq 1 ]
