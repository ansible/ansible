#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

job="${args[1]}"

# python versions to test in order
# python 2.7 runs full tests while other versions run minimal tests
python_versions=(
    2.6
    3.5
    3.6
    2.7
)

# shellcheck disable=SC2086
ansible-test windows-integration --explain ${CHANGED:+"$CHANGED"} 2>&1 | { grep ' windows-integration: .* (targeted)$' || true; } > /tmp/windows.txt

if [ -s /tmp/windows.txt ]; then
    echo "Detected changes requiring integration tests specific to Windows:"
    cat /tmp/windows.txt

    if [ "${job}" != "1" ]; then
        echo "Nothing to do, all Windows tests will run under TEST=windows/1 instead."
        exit 0
    fi

    echo "Running Windows integration tests for multiple versions concurrently."

    target="windows/ci/"

    platforms=(
        --windows 2008-SP2
        --windows 2008-R2_SP1
        --windows 2012-RTM
        --windows 2012-R2_RTM
    )
else
    echo "No changes requiring integration tests specific to Windows were detected."
    echo "Running Windows integration tests for a single version only."

    target="windows/ci/group${job}/"

    platforms=(
        --windows 2012-R2_RTM
    )
fi

retry.py pip install tox --disable-pip-version-check

for version in "${python_versions[@]}"; do
    # clean up between test runs until we switch from --tox to --docker
    rm -rf ~/.ansible/{cp,pc,tmp}/

    if [ "${job}" == "1" ] || [ "${version}" == "2.7" ]; then
        if [ "${version}" == "2.7" ]; then
            # full tests for python 2.7
            ci="${target}"
        else
            # minimal tests for other python versions
            ci="windows/ci/minimal/"
        fi

        # shellcheck disable=SC2086
        ansible-test windows-integration --color -v --retry-on-error "${ci}" --tox --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
            "${platforms[@]}"
    fi
done
