#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

platform="${args[0]}"
version="${args[1]}"
target="posix/ci/group${args[2]}/"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
     --remote "${platform}/${version}" --remote-terminate always
