#!/usr/bin/env bash

set -eu -o pipefail
source virtualenv.sh
set +x
unset PYTHONPATH
export PIP_DISABLE_PIP_VERSION_CHECK=1
export SETUPTOOLS_USE_DISTUTILS=stdlib

base_dir="$(dirname "$(dirname "$(dirname "$(dirname "${OUTPUT_DIR}")")")")"
bin_dir="$(dirname "$(command -v pip)")"


# NOTE: pip < 20 doesn't support in-tree build backends. This is why, we
# NOTE: pre-build a compatible sdist that has it self-eliminated. Following
# NOTE: installs from that artifact will use the setuptools-native backend
# NOTE: instead, as a compatibility measure for ancient environments.
pip install 'build ~= 0.10.0'
python -m build --sdist --outdir="${OUTPUT_DIR}"/dist "${base_dir}"

# deps are already installed, using --no-deps to avoid re-installing them
pip install "${OUTPUT_DIR}"/dist/ansible-core-*.tar.gz --no-deps
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
