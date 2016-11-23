#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

target="windows/ci/group${args[1]}/"

ansible-test integration --explain 2>&1 | grep ' integration: ' | grep -v ' integration: none$' > /tmp/posix.txt

if [ -s /tmp/posix.txt ]; then
    echo "Detected changes requiring integration tests which are not specific to Windows:"
    cat /tmp/posix.txt

    echo "Running Windows integration tests for a single version only."
    ansible-test windows-integration --color -v "${target}" --requirements \
        --windows 2012-R2_RTM
else
    echo "Running Windows integration tests for multiple versions concurrently."
    ansible-test windows-integration --color -v "${target}" --requirements \
        --windows 2008-SP2 \
        --windows 2008-R2_SP1 \
        --windows 2012-RTM \
        --windows 2012-R2_RTM \
        --windows 2016-English-Full-Base
fi
