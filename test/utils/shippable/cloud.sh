#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

image="${args[1]}"
target="posix/ci/cloud/group${args[2]}/"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --docker "${image}" --changed-all-target "${target}smoketest/"
