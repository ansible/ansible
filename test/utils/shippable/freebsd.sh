#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

platform="${args[0]}"
version="${args[1]}"
target="posix/ci/"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" --remote "${platform}/${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --exclude "posix/ci/cloud/"
