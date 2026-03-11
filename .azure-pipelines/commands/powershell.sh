#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

target_type="${args[1]}"
platform="${args[2]}"
powershell="${args[3]}"

if [ "${#args[@]}" -gt 4 ]; then
    target="shippable/powershell/group${args[4]}/"
else
    target="shippable/powershell/"
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --controller "docker:default,python=default" \
    --target "${target_type}:${platform},powershell=${powershell}"
