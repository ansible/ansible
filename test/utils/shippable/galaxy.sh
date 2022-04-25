#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

python="${args[1]}"
group="${args[2]}"

target="shippable/galaxy/group${group}/"

stage="${S:-prod}"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --remote-terminate always --remote-stage "${stage}" --docker --python "${python}"
