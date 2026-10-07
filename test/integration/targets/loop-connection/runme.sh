#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook main.yml -e "dummy_connection_log=${OUTPUT_DIR}/connection.log" "$@"
