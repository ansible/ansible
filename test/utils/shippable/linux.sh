#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

image="${args[1]}"

if [ "${#args[@]}" -gt 2 ]; then
    target="shippable/posix/group${args[2]}/"
else
    target="shippable/posix/"
fi

# detect the post migration ansible/ansible repo and enable test support plugins
if [ -f lib/ansible/config/routing.yml ]; then
    # this option is only useful for ansible/ansible (not collections) and should not be used prior to migration (except for incidental tests)
    enable_test_support=--enable-test-support
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    ${enable_test_support:+"$enable_test_support"} \
    --docker "${image}"
