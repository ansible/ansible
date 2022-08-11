#!/usr/bin/env bash

source ../collection/setup.sh

vendor_dir="$(python -c 'import pathlib, ansible._vendor; print(pathlib.Path(ansible._vendor.__file__).parent)')"

cleanup() {
    rm -rf "${vendor_dir}/demo/"
}

trap cleanup EXIT

# Verify that packages installed in the vendor directory are not available to the import test.
# If they are, the vendor logic will generate a warning which will be turned into an error.
# Testing this requires at least two plugins (not modules) to be run through the import test.

mkdir "${vendor_dir}/demo/"
touch "${vendor_dir}/demo/__init__.py"

ansible-test sanity --test import --color --truncate 0 plugins/lookup/vendor1.py plugins/lookup/vendor2.py "${@}"
