#!/usr/bin/env bash

set -eux

[ -f "${INVENTORY}" ]

ansible-playbook test_connection.yml -i "${INVENTORY}" "$@"

# Check that connection vars do not appear in the output
# https://github.com/ansible/ansible/pull/70853
trap "rm out.txt" EXIT

ansible all -i "${INVENTORY}" -m set_fact -a "testing=value" -v | tee out.txt
if grep 'ansible_host' out.txt
then
    echo "FAILURE: Connection vars in output"
    exit 1
else
    echo "SUCCESS: Connection vars not found"
fi

ansible-playbook test_reset_connection.yml -i "${INVENTORY}" "$@"
