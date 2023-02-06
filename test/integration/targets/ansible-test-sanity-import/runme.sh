#!/usr/bin/env bash

set -eu

# Create test scenarios at runtime that do not pass sanity tests.
# This avoids the need to create ignore entries for the tests.

mkdir -p ansible_collections/ns/col/plugins/lookup

(
  cd ansible_collections/ns/col/plugins/lookup

  echo "import sys; sys.stdout.write('unwanted stdout')" > stdout.py # stdout: unwanted stdout
  echo "import sys; sys.stderr.write('unwanted stderr')" > stderr.py # stderr: unwanted stderr
)

source ../collection/setup.sh

# Run regular import sanity tests.

ansible-test sanity --test import --color --failure-ok --lint --python "${ANSIBLE_TEST_PYTHON_VERSION}" "${@}" 1> actual-stdout.txt 2> actual-stderr.txt
diff -u "${TEST_DIR}/expected.txt" actual-stdout.txt
grep -f "${TEST_DIR}/expected.txt" actual-stderr.txt

# Run import sanity tests which require modifications to the source directory.

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
