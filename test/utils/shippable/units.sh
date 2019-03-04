#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"

if [[ "${COVERAGE:-}" ]]; then
    # increase timeout for unit tests when code coverage is enabled
    ansible-test env --timeout 105 --color -v
else
    # limit unit test runtime when not collecting code coverage
    ansible-test env --timeout 15 --color -v
fi

# shellcheck disable=SC2086
ansible-test units --color -v --docker default --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
