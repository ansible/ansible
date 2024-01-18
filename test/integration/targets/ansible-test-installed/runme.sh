#!/usr/bin/env bash

base_dir="$(dirname "$(dirname "$(dirname "$(dirname "${OUTPUT_DIR}")")")")"
bin_dir="${base_dir}/bin"

source ../collection/setup.sh
source virtualenv.sh

unset PYTHONPATH

# find the bin entry points to test
ls "${bin_dir}" > tests/integration/targets/installed/entry-points.txt

# deps are already installed, using --no-deps to avoid re-installing them
pip install "${base_dir}" --disable-pip-version-check --no-deps

# verify entry point generation without delegation
ansible-test integration --color --truncate 0 "${@}"

# verify entry point generation with same-host delegation
ansible-test integration --venv --color --truncate 0 "${@}"
