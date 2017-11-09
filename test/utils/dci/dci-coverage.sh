#!/bin/bash -eux

set -o pipefail

# Script invoked by DCI-Agents hooks/post-running.yml

# Platform: $1 = (ios, openvswitch, vyos, ...)
# Branch: $2 = (devel, stable-2.4, ...)

test="dci/$1"
branch="$2"

if find test/results/coverage/ -mindepth 1 -name '.*' -prune -o -print -quit | grep -q .; then
    stub=""

    # shellcheck disable=SC2086
    test/runner/ansible-test coverage xml -v --requirements --group-by command --group-by version ${stub:+"$stub"}

    # upload coverage report to codecov.io
    for file in test/results/reports/coverage=*.xml; do
        flags="${file##*/coverage=}"
        flags="${flags%.xml}"
        flags="${flags//=/,}"
        flags="${flags//[^a-zA-Z0-9_,]/_}"

        bash <(curl -s https://codecov.io/bash) \
            -f "${file}" \
            -F "${flags}" \
            -n "${test}" \
            -t 83cd8957-dc76-488c-9ada-210dcea51633 \
            -X coveragepy \
            -X gcov \
            -X fix \
            -X search \
            -X xcode \
            -K \
            -B "$branch" \
            -r "ansible/ansible" \
        || echo "Failed to upload code coverage report to codecov.io: ${file}"
    done
fi
