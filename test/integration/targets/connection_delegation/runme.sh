#!/usr/bin/env bash

set -ux

echo "Checking if sshpass is present"
which sshpass 2>&1 || exit 0
echo "sshpass is present, continuing with test"

sshpass -p my_password ansible-playbook -i inventory.ini test.yml -k "$@"
