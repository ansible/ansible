#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

job="${args[1]}"

ansible-test windows-integration --explain 2>&1 | { grep ' windows-integration: .* (targeted)$' || true; } > /tmp/windows.txt

if [ -s /tmp/windows.txt ]; then
    echo "Detected changes requiring integration tests specific to Windows:"
    cat /tmp/windows.txt

    if [ "${job}" != "1" ]; then
        echo "Nothing to do, all Windows tests will run under TEST=windows/1 instead."
        exit 0
    fi

    echo "Running Windows integration tests for multiple versions concurrently."

    target="windows/ci/"

    ansible-test windows-integration --color -v --retry-on-error "${target}" --requirements \
        --windows 2008-SP2 \
        --windows 2008-R2_SP1 \
        --windows 2012-RTM \
        --windows 2012-R2_RTM \

else
    echo "No changes requiring integration tests specific to Windows were detected."
    echo "Running Windows integration tests for a single version only."

    target="windows/ci/group${job}/"

    ansible-test windows-integration --color -v --retry-on-error "${target}" --requirements \
        --windows 2012-R2_RTM
fi
