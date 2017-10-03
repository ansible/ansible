#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

image="ansible/ansible:${args[1]}"
target="posix/ci/group${args[2]}/"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
     --docker "${image}"
