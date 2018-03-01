#!/bin/bash -eux

set -o pipefail

ansible_repo_url="https://github.com/ansible/ansible.git"

build_dir="${SHIPPABLE_BUILD_DIR}"
repo="${REPO_NAME}"

case "${repo}" in
    "ansible-modules-core")
        this_module_group="core"
        other_module_group="extras"
        ;;
    "ansible-modules-extras")
        this_module_group="extras"
        other_module_group="core"
        ;;
    *)
        echo "Unsupported repo name: ${repo}"
        exit 1
        ;;
esac

modules_tmp_dir="${build_dir}.tmp"
this_modules_dir="${build_dir}/lib/ansible/modules/${this_module_group}"
other_modules_dir="${build_dir}/lib/ansible/modules/${other_module_group}"

cd /
mv "${build_dir}" "${modules_tmp_dir}"
git clone "${ansible_repo_url}" "${build_dir}"
cd "${build_dir}"
rmdir "${this_modules_dir}"
mv "${modules_tmp_dir}" "${this_modules_dir}"
mv "${this_modules_dir}/shippable" "${build_dir}"
git submodule init "${other_modules_dir}"
git submodule sync "${other_modules_dir}"
git submodule update "${other_modules_dir}"

pip install -r lib/ansible/modules/${this_module_group}/test/utils/shippable/docs-requirements.txt --upgrade
pip list

source hacking/env-setup

docs_status=0

PAGER=/bin/cat \
    ANSIBLE_DEPRECATION_WARNINGS=false \
    bin/ansible-doc -l \
    2>/tmp/ansible-doc.err || docs_status=$?

if [ -s /tmp/ansible-doc.err ]; then
    # report warnings as errors
    echo "Output from 'ansible-doc -l' on stderr is considered an error:"
    cat /tmp/ansible-doc.err
    exit 1
fi

if [ "${docs_status}" -ne 0 ]; then
    echo "Running 'ansible-doc -l' failed with no output on stderr and exit code: ${docs_status}"
    exit 1
fi
