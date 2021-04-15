#!/usr/bin/env bash

# #74270 -- ensure we escape directory names before passing to re.compile()
# particularly in module_common.

set -eux

lib_path=$(python -c 'import os, ansible; print(os.path.dirname(os.path.dirname(ansible.__file__)))')
bad_dir="${OUTPUT_DIR}/ansi[ble"

mkdir "${bad_dir}"
cp -a "${lib_path}" "${bad_dir}"

PYTHONPATH="${bad_dir}/lib" ansible -m ping localhost -i ../../inventory "$@"
rm -rf "${bad_dir}"
