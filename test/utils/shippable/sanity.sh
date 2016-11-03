#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

install_deps="${INSTALL_DEPS:-}"

cd "${source_root}"

# FIXME REPOMERGE: No need to checkout ansible
build_dir=$(mktemp -d)
trap 'rm -rf "${build_dir}"' EXIT

git clone "https://github.com/ansible/ansible.git" "${build_dir}" --recursive
source "${build_dir}/hacking/env-setup"
# REPOMERGE: END

if [ "${install_deps}" != "" ]; then
    add-apt-repository ppa:fkrull/deadsnakes
    apt-add-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
    apt-get update -qq

    apt-get install -qq shellcheck python2.4

    # Install dependencies for ansible and validate_modules
    pip install -r "${build_dir}/test/utils/shippable/sanity-requirements.txt" --upgrade
    pip list

fi

validate_modules="${build_dir}/test/sanity/validate-modules/validate-modules"

python2.4 -m compileall -fq   -x "($(printf %s "$(< "test/utils/shippable/sanity-skip-python24.txt"))" | tr '\n' '|')" .
python2.6 -m compileall -fq .
python2.7 -m compileall -fq .
python3.5 -m compileall -fq .

ANSIBLE_DEPRECATION_WARNINGS=false \
    "${validate_modules}" --exclude '/utilities/|/shippable(/|$)' .

shellcheck \
    test/utils/shippable/*.sh
