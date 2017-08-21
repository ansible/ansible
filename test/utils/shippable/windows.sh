#!/bin/bash -eux

set -o pipefail

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

    echo "Running Windows integration tests for multiple versions concurrently."

    platforms=(
        --windows 2008-SP2
        --windows 2008-R2_SP1
        --windows 2012-RTM
        --windows 2012-R2_RTM
    )
else
    echo "No changes requiring integration tests specific to Windows were detected."
    echo "Running Windows integration tests for a single version only."

    platforms=(
        --windows 2012-R2_RTM
    )
fi

retry.py pip install tox --disable-pip-version-check

for version in "${python_versions[@]}"; do
    # clean up between test runs until we switch from --tox to --docker
    rm -rf ~/.ansible/{cp,pc,tmp}/

    changed_all_target="all"

    if [ "${version}" == "2.7" ]; then
        # smoketest tests for python 2.7
        if [ "${CHANGED}" ]; then
            # with change detection enabled run tests for anything changed
            # use the smoketest tests for any change that triggers all tests
            ci="windows/ci/"
            changed_all_target="windows/ci/smoketest/"
        else
            # without change detection enabled run only smoketest tests
            ci="windows/ci/smoketest/"
        fi
    else
        # minimal tests for other python versions
        ci="windows/ci/minimal/"
    fi

    # shellcheck disable=SC2086
    ansible-test windows-integration --color -v --retry-on-error "${ci}" --tox --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
        "${platforms[@]}" --changed-all-target "${changed_all_target}"
done
