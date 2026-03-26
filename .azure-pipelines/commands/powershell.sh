#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

powershell="${args[1]}"

if [ "${#args[@]}" -gt 2 ]; then
    target="shippable/powershell/group${args[2]}/"
else
    target="shippable/powershell/"
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --controller "docker:default,python=default" \
    --target "docker:default,powershell=${powershell}"
