#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

cloud="${args[0]}"
python="${args[1]}"
group="${args[2]}"

target="shippable/${cloud}/group${group}/"

stage="${S:-prod}"

changed_all_target="shippable/${cloud}/smoketest/"

if ! ansible-test integration "${changed_all_target}" --list-targets > /dev/null 2>&1; then
    # no smoketest tests are available for this cloud
    changed_all_target="none"
fi

if [ "${group}" == "1" ]; then
    # only run smoketest tests for group1
    changed_all_mode="include"
else
    # smoketest tests already covered by group1
    changed_all_mode="exclude"
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --remote-terminate always --remote-stage "${stage}" \
    --docker --python "${python}" --changed-all-target "${changed_all_target}" --changed-all-mode "${changed_all_mode}"
