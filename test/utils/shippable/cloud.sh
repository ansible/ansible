#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

image="${args[1]}"
python="${args[2]}"
target="posix/ci/cloud/group${args[3]}/"

stage="${S:-prod}"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --remote-terminate always --remote-stage "${stage}" \
    --docker "${image}" --python "${python}" --changed-all-target "${target}smoketest/"
