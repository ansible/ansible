#!/usr/bin/env bash

set -eux

source virtualenv.sh

mkdir -p "${JUNIT_OUTPUT_DIR}"  # ensure paths relative to this path work

cli_doc="${JUNIT_OUTPUT_DIR}/../../../packaging/cli-doc"
build="${cli_doc}/build.py"
template="template.j2"

# Test `rst` command

pip install jinja2

rst_dir="${OUTPUT_DIR}/rst"

python.py "${build}" rst --output-dir "${rst_dir}" && ./verify.py "${rst_dir}"
python.py "${build}" rst --output-dir "${rst_dir}" --template "${template}" && ./verify.py "${rst_dir}"

# Test `man` command (and the argcomplete code path)

pip install docutils argcomplete

man_dir="${OUTPUT_DIR}/man"

python.py "${build}" man --output-dir "${man_dir}" && ./verify.py "${man_dir}"
python.py "${build}" man --output-dir "${man_dir}" --template "${template}" && ./verify.py "${man_dir}"

# Test `json` command

python.py "${build}" json --output-file docs.json && ls -l docs.json

# Ensure complete coverage of the main conditional

echo "import sys; sys.path.insert(0, '${cli_doc}'); import build" > cover.py
python.py cover.py
