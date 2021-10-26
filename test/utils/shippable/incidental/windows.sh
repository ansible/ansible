#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"

target="shippable/windows/incidental/"

stage="${S:-prod}"
provider="${P:-default}"

# python versions to test in order
IFS=' ' read -r -a python_versions <<< \
    "$(PYTHONPATH="${PWD}/test/lib" python -c 'from ansible_test._internal import constants; print(" ".join(constants.CONTROLLER_PYTHON_VERSIONS))')"

# python version to run full tests on while other versions run minimal tests
python_default="$(PYTHONPATH="${PWD}/test/lib" python -c 'from ansible_test._internal import constants; print(constants.CONTROLLER_MIN_PYTHON_VERSION)')"

# version to test when only testing a single version
single_version=2012-R2

# shellcheck disable=SC2086
ansible-test windows-integration --list-targets -v ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} > /tmp/explain.txt 2>&1 || { cat /tmp/explain.txt && false; }
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
    if [ "${version}" == "${python_default}" ]; then
        # full tests
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
