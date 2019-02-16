#!/usr/bin/env bash

set -eu
set -o pipefail

container="$1"
files_from="$2"
destination_dir="$3"

docker exec "${container}" mkdir -p "${destination_dir}"

tar cf - --no-recursion --files-from="${files_from}" \
    | docker exec -i "${container}" tar xf - -C "${destination_dir}" --warning=no-unknown-keyword
