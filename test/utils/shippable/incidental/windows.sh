#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"

target="shippable/windows/incidental/"

stage="${S:-prod}"
provider="${P:-default}"

# python versions to test in order
# python 2.7 runs full tests while other versions run minimal tests
python_versions=(
    3.5
    3.6
    3.7
    3.8
    2.7
)

# version to test when only testing a single version
single_version=2012-R2

# shellcheck disable=SC2086
ansible-test windows-integration --explain ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} > /tmp/explain.txt 2>&1 || { cat /tmp/explain.txt && false; }
{ grep ' windows-integration: .* (targeted)$' /tmp/explain.txt || true; } > /tmp/windows.txt

if [ -s /tmp/windows.txt ] || [ "${CHANGED:+$CHANGED}" == "" ]; then
    echo "Detected changes requiring integration tests specific to Windows:"
    cat /tmp/windows.txt

    echo "Running Windows integration tests for multiple versions concurrently."

    platforms=(
        --windows "${version}"
    )
else
    echo "No changes requiring integration tests specific to Windows were detected."
    echo "Running Windows integration tests for a single version only: ${single_version}"

    if [ "${version}" != "${single_version}" ]; then
        echo "Skipping this job since it is for: ${version}"
        exit 0
    fi

    platforms=(
        --windows "${version}"
    )
fi

for version in "${python_versions[@]}"; do
    if [ "${version}" == "2.7" ]; then
        # full tests for python 2.7
        ci="${target}"
    else
        # minimal tests for other python versions
        ci="incidental_win_ping"
    fi

    # terminate remote instances on the final python version tested
    if [ "${version}" = "${python_versions[-1]}" ]; then
        terminate="always"
    else
        terminate="never"
    fi

    # shellcheck disable=SC2086
    ansible-test windows-integration --color -v --retry-on-error "${ci}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
        "${platforms[@]}" \
        --docker default --python "${version}" \
        --remote-terminate "${terminate}" --remote-stage "${stage}" --remote-provider "${provider}"
done
