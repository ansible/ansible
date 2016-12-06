#!/bin/bash -eux

set -o pipefail

ansible_repo_url="https://github.com/ansible/ansible.git"

is_pr="${IS_PULL_REQUEST}"
build_dir="${SHIPPABLE_BUILD_DIR}"
repo="${REPO_NAME}"

if [ "${is_pr}" != "true" ]; then
    echo "Module integration tests are only supported on pull requests."
    exit 0
fi

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

pip install -r test/utils/shippable/modules/generate-tests-requirements.txt --upgrade
pip list

source hacking/env-setup

test/utils/shippable/modules/generate-tests "${this_module_group}" --verbose --output /tmp/integration.sh >/dev/null

if [ -f /tmp/integration.sh ]; then
    /bin/bash -eux /tmp/integration.sh
fi
