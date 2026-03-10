#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

powershell="${args[0]}"
pyver=default

if [ "${#args[@]}" -gt 1 ]; then
    target="shippable/powershell/group${args[1]}/"
else
    target="shippable/powershell/"
fi

# Add this once I've figured out how to get the support/integration/collections
# into the controller
# --controller "docker:default,python=${pyver}"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --target "docker:ubuntu2404,powershell=${powershell}"
