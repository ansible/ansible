#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

platform="${args[0]}"
version="${args[1]}"
pyver=default

# check for explicit python version like 8.3@3.8
declare -a splitversion
IFS='@' read -ra splitversion <<< "$version"

if [ "${#splitversion[@]}" -gt 1 ]; then
    version="${splitversion[0]}"
    pyver="${splitversion[1]}"
fi

group="${args[2]}"

declare -a group_args
IFS='@' read -ra group_args <<< "${group}"

arch="${group_args[0]}"
group="${group_args[1]}"

echo "Group ${group} on ${arch}"

target="shippable/posix/group${group}/"

stage="${S:-prod}"
provider="${P:-default}"

if [ "${arch}" = "c7a" ]; then
  arch="x86_64"
  stage="dev"
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --python "${pyver}" --remote "${platform}/${version}" --remote-terminate always --remote-stage "${stage}" --remote-provider "${provider}" \
    --remote-arch "${arch}" \
