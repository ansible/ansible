#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

image="ansible/ansible:${args[1]}"
target="posix/ci/cloud/"

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" --docker "${image}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --changed-all-target 'posix/ci/cloud/vcenter/'
