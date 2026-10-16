#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook main.yml -e "dummy_connection_log=${OUTPUT_DIR}/connection.log" "$@"

ansible-playbook delegation.yml -i delegation_inventory.ini -e "dummy_connection_log=${OUTPUT_DIR}/connection.log" "$@"

# local displays this message each time it connects
ansible-playbook builtin_fqcn.yml -vvv "$@" | tee "${OUTPUT_DIR}/builtin_fqcn.out"
test "$(grep -c 'ESTABLISH LOCAL CONNECTION' "${OUTPUT_DIR}/builtin_fqcn.out")" -eq 1
