#!/bin/bash -eux

set -o pipefail

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

test_flags="${TEST_FLAGS:-}"
test_platform="${PLATFORM}"
test_version="${VERSION}"

test_target=(${TARGET})

instance_id="${INSTANCE_ID:-}"
start_instance=

if [ "${instance_id}" == "" ]; then
    instance_id=$(python -c 'import uuid; print(uuid.uuid4())')
    start_instance=1
fi

# Set this to a non-empty value to skip immediate termination of the remote instance after tests finish.
# The remote instance will still be auto-terminated when the remote time limit is reached.
keep_instance="${KEEP_INSTANCE:-}"

# Force ansible color output by default.
# To disable color force mode use FORCE_COLOR=0
force_color="${FORCE_COLOR:-1}"

if [ "${SHIPPABLE:-}" = "true" ]; then
    test_auth="shippable"
else
    test_auth="remote"
fi

case "${test_platform}" in
    "windows")
        ci_endpoint="https://14blg63h2i.execute-api.us-east-1.amazonaws.com"
        ;;
    "freebsd")
        ci_endpoint="https://14blg63h2i.execute-api.us-east-1.amazonaws.com"
        ;;
    "osx")
        ci_endpoint="https://osx.testing.ansible.com"
        ;;
    *)
        echo "unsupported platform: ${test_platform}"
        exit 1
        ;;
esac

env

case "${test_platform}" in
    "windows")
        args=""
        ;;
    *)
        ssh_key="${HOME}/.ssh/id_rsa"
        args="--public-key=${ssh_key}.pub"
        if [ ! -f "${ssh_key}.pub" ]; then
            ssh-keygen -q -t rsa -N '' -f "${ssh_key}"
        fi
        ;;
esac

pre_cleanup=

function cleanup
{
    if [ "${pre_cleanup}" != '' ]; then
        "${pre_cleanup}"
    fi

    if [ "${keep_instance}" = '' ]; then
        "${source_root}/test/utils/shippable/ansible-core-ci" --endpoint "${ci_endpoint}" -v stop "${instance_id}"
    fi

    echo "instance_id: ${instance_id}"
}

trap cleanup EXIT INT TERM

if [ ${start_instance} ]; then
    # shellcheck disable=SC2086
    "${source_root}/test/utils/shippable/ansible-core-ci" --endpoint "${ci_endpoint}" -v \
        start --id "${instance_id}" "${test_auth}" "${test_platform}" "${test_version}" ${args}
fi

pip install pip --upgrade
pip install "${source_root}" --upgrade
pip install -r "${source_root}/test/utils/shippable/remote-requirements.txt" --upgrade
pip list

cd "${source_root}"
source hacking/env-setup
cd test/integration

case "${test_platform}" in
    "windows")
        inventory_template="${source_root}/test/integration/inventory.winrm.template"
        inventory_file="${source_root}/test/integration/inventory.winrm"
        ping_module="win_ping"
        ping_args=""
        ping_host="windows"
        test_function="test_windows"
        ;;
    *)
        inventory_template="${source_root}/test/integration/inventory.remote.template"
        inventory_file="${source_root}/test/integration/inventory.remote"
        ping_module="raw"
        ping_args="id"
        ping_host="remote"
        test_function="test_remote"
        ;;
esac

"${source_root}/test/utils/shippable/ansible-core-ci" --endpoint "${ci_endpoint}" -v \
    get "${instance_id}" \
    --template "${inventory_template}" \
    > "${inventory_file}" \

# hack to make sure instance is responding before beginning tests
n=60
for i in $(seq 1 ${n}); do
    echo "Verifying host is responding ($i of $n)"
    if \
        ANSIBLE_SSH_ARGS='' \
        ANSIBLE_HOST_KEY_CHECKING=False \
        ANSIBLE_FORCE_COLOR="${force_color}" \
        ansible -m "${ping_module}" -a "${ping_args}" -i "${inventory_file}" "${ping_host}"; then
        break
    fi
    sleep 5
done

test_windows() {
    JUNIT_OUTPUT_DIR="${source_root}/shippable/testresults" \
        ANSIBLE_FORCE_COLOR="${force_color}" \
        ANSIBLE_CALLBACK_WHITELIST=junit \
        TEST_FLAGS="${test_flags}" \
        LC_ALL=en_US.utf-8 \
        make "${test_target[@]}"
}

test_remote() {
    endpoint=$("${source_root}/test/utils/shippable/ansible-core-ci" --endpoint "${ci_endpoint}" get \
        "${instance_id}" \
        --template <(echo "@ansible_user@@ansible_host"))
    ssh_port=$("${source_root}/test/utils/shippable/ansible-core-ci" --endpoint "${ci_endpoint}" get \
        "${instance_id}" \
        --template <(echo "@ansible_port"))

(
cat <<EOF
env \
PLATFORM='${test_platform}' \
REPOSITORY_URL='${REPOSITORY_URL:-}' \
REPO_NAME='${REPO_NAME:-}' \
PULL_REQUEST='${PULL_REQUEST:-}' \
BRANCH='${BRANCH:-}' \
COMMIT='${COMMIT:-}' \
FORCE_COLOR='${force_color}' \
TARGET='${test_target[*]}' \
TEST_FLAGS='${test_flags}' \
/bin/sh -e /tmp/remote-integration.sh
EOF
) > /tmp/remote-script.sh

(
cat <<EOF
put "${source_root}/test/utils/shippable/remote-integration.sh" "/tmp/remote-integration.sh"
put "/tmp/remote-script.sh" "/tmp/remote-script.sh"
EOF
) | sftp -b - -o StrictHostKeyChecking=no -P "${ssh_port}" "${endpoint}"

    pre_cleanup=test_remote_cleanup

    case "${test_platform}" in
        "osx")
            become="sudo -i PATH=/usr/local/bin:\$PATH"
            ;;
        *)
            become="su -l root -c"
            ;;
    esac

    ssh -p "${ssh_port}" "${endpoint}" "${become}" "'chmod +x /tmp/remote-script.sh; /tmp/remote-script.sh'"
}

test_remote_cleanup() {
    scp -r -P "${ssh_port}" "${endpoint}:/tmp/shippable" "${source_root}"
}

"${test_function}"
