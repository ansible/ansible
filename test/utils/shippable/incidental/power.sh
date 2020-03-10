#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

platform="${args[1]}"
version="${args[2]}"

target="shippable/posix/incidental/"

stage="${S:-prod}"
# Endpoint is ibmvpc, but this reflect a service that can be leverage
# to spawn both x86 and power arch. Making the provider being power
# is more meaningful to what is being done here
provider="${P:-power}"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --remote "${platform}/${version}" --remote-terminate always --remote-stage "${stage}" --remote-provider "${provider}"
