#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

target="windows/ci/group${args[1]}/"

ansible-test windows-integration --explain 2>&1 | grep ' windows-integration: .* (targeted)$' > /tmp/windows.txt

if [ ! -s /tmp/windows.txt ]; then
    echo "Detected changes requiring integration tests specific to Windows:"
    cat /tmp/windows.txt
    echo "Running Windows integration tests for multiple versions concurrently."

    ansible-test windows-integration --color -v --retry-on-error "${target}" --requirements \
        --windows 2008-SP2 \
        --windows 2008-R2_SP1 \
        --windows 2012-RTM \
        --windows 2012-R2_RTM \
        --windows 2016-English-Full-Base
else
    echo "No changes requiring integration tests specific to Windows were detected."
    echo "Running Windows integration tests for a single version only."

    ansible-test windows-integration --color -v --retry-on-error "${target}" --requirements \
        --windows 2012-R2_RTM
fi
