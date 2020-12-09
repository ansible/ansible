#!/usr/bin/env bash

set -eux

[ -f "${INVENTORY}" ]

# Run connection tests with both the default and C locale.

                ansible-playbook test_connection.yml -i "${INVENTORY}" "$@"
LC_ALL=C LANG=C ansible-playbook test_connection.yml -i "${INVENTORY}" "$@"

ansible-playbook test_reset_connection.yml -i "${INVENTORY}" "$@"