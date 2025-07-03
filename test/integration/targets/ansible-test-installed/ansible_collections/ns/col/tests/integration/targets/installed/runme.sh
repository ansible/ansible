#!/usr/bin/env bash
# This test ensures that the bin entry points created by ansible-test work
# when ansible-test is running from an install instead of from source.

set -eux

# The third PATH entry is the injected bin directory created by ansible-test.
bin_dir="$(python -c 'import os; print(os.environ["PATH"].split(":")[2])')"

while IFS= read -r name
do
    bin="${bin_dir}/${name}"

    entry_point="${name//ansible-/}"
    entry_point="${entry_point//ansible/adhoc}"

    echo "=== ${name} (${entry_point})=${bin} ==="

    if [ "${name}" == "ansible-test" ]; then
        echo "skipped - ansible-test does not support self-testing from an install"
    else
        "${bin}" --version | tee /dev/stderr | grep -Eo "(^${name}\ \[core\ .*|executable location = ${bin}$)"
    fi
done < entry-points.txt
