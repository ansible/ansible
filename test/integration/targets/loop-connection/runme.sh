#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook main.yml -e "dummy_connection_log=${OUTPUT_DIR}/connection.log" "$@"

ansible-playbook delegation.yml -i delegation_inventory.ini -e "dummy_connection_log=${OUTPUT_DIR}/connection.log" "$@"
