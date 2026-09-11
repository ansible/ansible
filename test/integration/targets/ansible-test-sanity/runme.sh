#!/usr/bin/env bash

set -eux

source ./fix_filtering.sh

ansible-test sanity --color --allow-disabled -e "${@}"

set +x

source ../collection/setup.sh

set -x

ansible-test sanity --color --truncate 0 "${@}"
