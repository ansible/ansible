#!/bin/bash -eux

# join_by found here:
# https://stackoverflow.com/questions/1527049/how-can-i-join-elements-of-an-array-in-bash
function join_by { local IFS="$1"; shift; echo "$*"; }

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

script="${args[1]}"
test=$(join_by / ${args[@]:1})

ANSIBLE_PROCESS_MODEL=threading test/utils/shippable/${script}.sh "${test}"
