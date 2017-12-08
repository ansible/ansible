#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

platform="${args[0]}"
version="${args[1]}"

if [ "${#args[@]}" -gt 2 ]; then
    target="posix/ci/group${args[2]}/"
else
    target="posix/ci/"
fi

stage="${S:-prod}"
provider="${P:-default}"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --exclude "posix/ci/cloud/" \
    --remote "${platform}/${version}" --remote-terminate always --remote-stage "${stage}" --remote-provider "${provider}"
