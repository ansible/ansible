#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

test_flags="${TEST_FLAGS:-}"
test_platform="${PLATFORM}"
test_version="${VERSION}"

test_target=(${TARGET})

# Force ansible color output by default.
# To disable color force mode use FORCE_COLOR=0
force_color="${FORCE_COLOR:-1}"

env

instance_id=$("${source_root}/test/utils/shippable/ansible-core-ci" -v \
    start shippable "${test_platform}" "${test_version}")

pip install -r "${source_root}/test/utils/shippable/remote-requirements.txt" --upgrade
pip list

function cleanup
{
    "${source_root}/test/utils/shippable/ansible-core-ci" -v stop "${instance_id}"
}

trap cleanup EXIT INT TERM

cd "${source_root}"
source hacking/env-setup
cd test/integration

inventory_template="${source_root}/test/integration/inventory.winrm.template"
inventory_file="${source_root}/test/integration/inventory.winrm"

"${source_root}/test/utils/shippable/ansible-core-ci" -v \
    get "${instance_id}" \
    --template "${inventory_template}" \
    > "${inventory_file}" \

# hack to make sure windows instance is responding before beginning tests
n=20
for i in $(seq 1 ${n}); do
    echo "Verifying host is responding ($i of $n)"
    if ANSIBLE_FORCE_COLOR="${force_color}" ansible -m win_ping -i "${inventory_file}" windows; then
        break
    fi
    sleep 3
done

JUNIT_OUTPUT_DIR="${source_root}/shippable/testresults" \
    ANSIBLE_FORCE_COLOR="${force_color}" \
    ANSIBLE_CALLBACK_WHITELIST=junit \
    TEST_FLAGS="${test_flags}" \
    LC_ALL=en_US.utf-8 \
    make "${test_target[@]}"
