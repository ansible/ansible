#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"

target="shippable/windows/incidental/"

stage="${S:-prod}"
provider="${P:-default}"

# python version to run full tests on while other versions run minimal tests
python_default="$(PYTHONPATH="${PWD}/test/lib" python -c 'from ansible_test._internal import constants; print(constants.CONTROLLER_MIN_PYTHON_VERSION)')"

# version to test when only testing a single version
single_version=2022

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

# shellcheck disable=SC2086
ansible-test windows-integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    "${platforms[@]}" \
    --docker default --python "${python_default}" \
    --remote-terminate always --remote-stage "${stage}" --remote-provider "${provider}"
