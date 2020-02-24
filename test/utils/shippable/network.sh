#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

platform="${args[0]}"
version="${args[1]}"

if [ "${#args[@]}" -gt 2 ]; then
    target="shippable/${platform}/group${args[2]}/"
else
    target="shippable/${platform}/"
fi

stage="${S:-prod}"
provider="${P:-default}"

# python versions to test in order
# all versions run full tests
python_versions=(
    2.7
    3.6
)

for python_version in "${python_versions[@]}"; do
    # terminate remote instances on the final python version tested
    if [ "${python_version}" = "${python_versions[-1]}" ]; then
        terminate="always"
    else
        terminate="never"
    fi

    # shellcheck disable=SC2086
    ansible-test network-integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
        --platform "${platform}/${version}" \
        --docker default --python "${python_version}" \
        --remote-terminate "${terminate}" --remote-stage "${stage}" --remote-provider "${provider}"
done
