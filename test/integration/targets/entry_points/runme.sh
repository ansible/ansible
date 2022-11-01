#!/usr/bin/env bash

set -eu -o pipefail
source virtualenv.sh
set +x
unset PYTHONPATH
export SETUPTOOLS_USE_DISTUTILS=stdlib

base_dir="$(dirname "$(dirname "$(dirname "$(dirname "${OUTPUT_DIR}")")")")"
bin_dir="$(dirname "$(command -v pip)")"

# deps are already installed, using --no-deps to avoid re-installing them
pip install "${base_dir}" --disable-pip-version-check --no-deps
# --use-feature=in-tree-build not available on all platforms

for bin in "${bin_dir}/ansible"*; do
    name="$(basename "${bin}")"

    entry_point="${name//ansible-/}"
    entry_point="${entry_point//ansible/adhoc}"

    echo "=== ${name} (${entry_point})=${bin} ==="

    if [ "${name}" == "ansible-test" ]; then
        "${bin}" --help | tee /dev/stderr | grep -Eo "^usage:\ ansible-test\ .*"
        python -m ansible "${entry_point}" --help | tee /dev/stderr | grep -Eo "^usage:\ ansible-test\ .*"
    else
        "${bin}" --version | tee /dev/stderr | grep -Eo "(^${name}\ \[core\ .*|executable location = ${bin}$)"
        python -m ansible "${entry_point}" --version | tee /dev/stderr | grep -Eo "(^${name}\ \[core\ .*|executable location = ${bin}$)"
    fi
done
