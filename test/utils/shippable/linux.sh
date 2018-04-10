#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

image="${args[1]}"

if [ "${#args[@]}" -gt 2 ]; then
    target="posix/ci/group${args[2]}/"
else
    target="posix/ci/"
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --exclude "posix/ci/cloud/" \
    --docker "${image}"
