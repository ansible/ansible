#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

cloud="${args[0]}"
python_version="${args[1]}"

target="shippable/${cloud}/incidental/"

stage="${S:-prod}"

# python versions to test in order
# all versions run full tests
python_versions=(
    2.7
    3.6
)

if [ "${python_version}" ]; then
    # limit tests to a single python version
    python_versions=("${python_version}")
fi

for python_version in "${python_versions[@]}"; do
    # terminate remote instances on the final python version tested
    if [ "${python_version}" = "${python_versions[-1]}" ]; then
        terminate="always"
    else
        terminate="never"
    fi

    # shellcheck disable=SC2086
    ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
        --remote-terminate "${terminate}" \
        --remote-stage "${stage}" \
        --docker --python "${python_version}"
done
