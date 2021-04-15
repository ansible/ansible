#!/usr/bin/env bash

# #74270 -- ensure we escape directory names before passing to re.compile()
# particularly in module_common.

set -eux

ansible_lib=$(python -c 'import os, ansible; print(os.path.dirname(ansible.__file__))')
bad_dir="${OUTPUT_DIR}/ansi[ble"

mkdir "${bad_dir}"
cp -a "${ansible_lib}" "${bad_dir}"

PYTHONPATH="${bad_dir}" ansible -m ping localhost -i ../../inventory "$@"
rm -rf "${bad_dir}"
