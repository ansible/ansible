#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

group="${args[1]}"

shippable.py

if [ "${BASE_BRANCH:-}" ]; then
    base_branch="origin/${BASE_BRANCH}"
else
    base_branch=""
fi

case "${group}" in
    1) options=(--skip-test pylint --skip-test ansible-doc --skip-test docs-build) ;;
    2) options=(--test pylint) ;;
    3) options=(--test ansible-doc --test docs-build) ;;
esac

# shellcheck disable=SC2086
ansible-test sanity --color -v --junit ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --docker --docker-keep-git --base-branch "${base_branch}" \
    "${options[@]}" --allow-disabled
