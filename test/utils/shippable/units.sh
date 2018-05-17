#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"

# shellcheck disable=SC2086
ansible-test units --color -v --docker default --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
