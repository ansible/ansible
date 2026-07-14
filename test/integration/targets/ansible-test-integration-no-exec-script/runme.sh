#!/usr/bin/env bash

source ../collection/setup.sh

set -x +o pipefail

ansible-test integration --venv --color --truncate 0 "${@}" 2>&1 | grep "Unable to run non-executable script"

echo "SUCCESS: Non-executable script error correctly handled."
