#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

group="${args[1]}"

group2_include=(
    ansible-doc
    changelog
    package-data
    pep8
    pylint
    validate-modules
)

group3_include=(
    docs-build
    sanity-docs
)

group1_exclude=(
    "${group2_include[@]}"
    "${group3_include[@]}"
)

options=()

case "${group}" in
    1)
        for name in "${group1_exclude[@]}"; do
            options+=(--skip-test "${name}")
        done
        ;;
    2)
        for name in "${group2_include[@]}"; do
            options+=(--test "${name}")
        done
        ;;
    3)
        for name in "${group3_include[@]}"; do
            options+=(--test "${name}")
        done
        ;;
esac

# shellcheck disable=SC2086
ansible-test sanity --color -v --junit ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --docker \
    "${options[@]}" --allow-disabled
