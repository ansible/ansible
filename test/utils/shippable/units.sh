#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"

if [[ "${COVERAGE:-}" == "--coverage" ]]; then
    timeout=99
else
    timeout=11
fi

ansible-test env --timeout "${timeout}" --color -v

if [[ "${version}" = "2.6" ]]; then
    # Python 2.6 is only supported for modules and module_utils.
    # Eventually this logic will move into ansible-test itself.
    targets=("test/units/(modules|module_utils)/")
else
    targets=()
fi

# shellcheck disable=SC2086
ansible-test units --color -v --docker default --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    "${targets[@]}" \
