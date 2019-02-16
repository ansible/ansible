#!/usr/bin/env bash

set -eu
set -o pipefail

container="$1"
source_dir="$2"
source="$3"
destination_dir="$4"

docker exec "${container}" tar c -C "${source_dir}" "${source}" \
    | tar ox -C "${destination_dir}"
