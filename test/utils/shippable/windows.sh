#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"
group="${args[2]}"

target="shippable/windows/group${group}/"

stage="${S:-prod}"
provider="${P:-default}"

# python versions to test in order
# python 2.7 runs full tests while other versions run minimal tests
python_versions=(
    2.6
    3.5
    3.6
    2.7
)

# version to test when only testing a single version
single_version=2012-R2

# shellcheck disable=SC2086
ansible-test windows-integration "${target}" --explain ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} 2>&1 \
    | { grep ' windows-integration: .* (targeted)$' || true; } > /tmp/windows.txt

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
    changed_all_target="all"

    if [ "${version}" == "2.7" ]; then
        # smoketest tests for python 2.7
        if [ "${CHANGED}" ]; then
            # with change detection enabled run tests for anything changed
            # use the smoketest tests for any change that triggers all tests
            ci="${target}"
            if [ "${target}" == "shippable/windows/group1/" ]; then
                # only run smoketest tests for group1
                changed_all_target="shippable/windows/smoketest/"
            else
                # smoketest tests already covered by group1
                changed_all_target="none"
            fi
        else
            # without change detection enabled run entire test group
            ci="${target}"
        fi
    else
        # only run minimal tests for group1
        if [ "${target}" != "shippable/windows/group1/" ]; then continue; fi
        # minimal tests for other python versions
        ci="shippable/windows/minimal/"
    fi

    # terminate remote instances on the final python version tested
    if [ "${version}" = "${python_versions[-1]}" ]; then
        terminate="always"
    else
        terminate="never"
    fi

    # shellcheck disable=SC2086
    ansible-test windows-integration --color -v --retry-on-error "${ci}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
        "${platforms[@]}" --changed-all-target "${changed_all_target}" \
        --docker default --python "${version}" \
        --remote-terminate "${terminate}" --remote-stage "${stage}" --remote-provider "${provider}"
done
