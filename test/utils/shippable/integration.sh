#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

test_image="${IMAGE:-ansible/ansible:centos7}"
test_privileged="${PRIVILEGED:-false}"
test_flags="${TEST_FLAGS:-}"
test_target="${TARGET:-all}"
test_ansible_dir="${TEST_ANSIBLE_DIR:-/root/ansible}"
test_python3="${PYTHON3:-}"

http_image="${HTTP_IMAGE:-ansible/ansible:httptester}"

# Keep the docker containers after tests complete.
# The default behavior is to always remove the containers.
# Set to "onfailure" to keep the containers only on test failure.
# Any other non-empty value will always keep the containers.
keep_containers="${KEEP_CONTAINERS:-}"

# Run the tests directly from the source directory shared with the container.
# The default behavior is to run the tests on a copy of the source.
# Copying the source isolates changes to the source between host and container.
# Set to any non-empty value to share the source.
share_source="${SHARE_SOURCE:-}"

# Force ansible color output by default.
# To disable color force mode use FORCE_COLOR=0
force_color="${FORCE_COLOR:-1}"

if [ "${SHIPPABLE_BUILD_DIR:-}" ]; then
    host_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
    controller_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
    share_source=1
    test_privileged=false # temporarily disabled to troubleshoot performance issues
else
    host_shared_dir="${source_root}"
    controller_shared_dir=""
fi

if [ -z "${share_source}" ]; then
    test_shared_dir="/shared"
else
    test_shared_dir="${test_ansible_dir}"
fi

container_id=
httptester_id=
tests_completed=

function show_environment
{
    docker ps

    if [ -d /home/shippable/cache ]; then
        ls -l /home/shippable/cache
    fi
}

function cleanup
{
    if [ "${controller_shared_dir}" ]; then
        cp -av "${controller_shared_dir}/shippable" "${SHIPPABLE_BUILD_DIR}"
        rm -rf "${controller_shared_dir}"
    fi

    if [ "${keep_containers}" == "onfailure" ] && [ "${tests_completed}" != "" ]; then
        keep_containers=
    fi

    if [ "${keep_containers}" == "" ]; then
        if [ "${container_id}" ]; then
            docker rm -f "${container_id}"
        fi

        if [ "${httptester_id}" ]; then
            docker rm -f "${httptester_id}"
        fi
    fi

    show_environment
}

trap cleanup EXIT INT TERM
docker images ansible/ansible
show_environment

if [ "${controller_shared_dir}" ]; then
    cp -a "${SHIPPABLE_BUILD_DIR}" "${controller_shared_dir}"
fi

httptester_id=$(docker run -d "${http_image}")
container_id=$(docker run -d \
    --env "ANSIBLE_FORCE_COLOR=${force_color}" \
    -v "/sys/fs/cgroup:/sys/fs/cgroup:ro" \
    -v "${host_shared_dir}:${test_shared_dir}" \
    --link="${httptester_id}:ansible.http.tests" \
    --link="${httptester_id}:sni1.ansible.http.tests" \
    --link="${httptester_id}:sni2.ansible.http.tests" \
    --link="${httptester_id}:fail.ansible.http.tests" \
    --privileged="${test_privileged}" \
    "${test_image}")

show_environment

skip=

if [ "${test_python3}" ]; then
    docker exec "${container_id}" ln -s /usr/bin/python3 /usr/bin/python
    docker exec "${container_id}" ln -s /usr/bin/pip3 /usr/bin/pip

    skip+=",$(tr '\n' ',' < "${source_root}/test/utils/shippable/python3-test-tag-blacklist.txt")"
fi

if [ "${test_privileged}" = 'false' ]; then
    skip+=",needs_privileged"
fi

if [ "${skip}" ]; then
    test_flags="--skip-tags ${skip} ${test_flags}"
fi

if [ -z "${share_source}" ]; then
    docker exec "${container_id}" cp -a "${test_shared_dir}" "${test_ansible_dir}"
fi

docker exec "${container_id}" \
    pip install -r "${test_ansible_dir}/test/utils/shippable/integration-requirements.txt" --upgrade

if [ "${test_python3}" ]; then
    docker exec "${container_id}" sed -i -f \
        "${test_ansible_dir}/test/utils/shippable/python3-test-target-blacklist.txt" \
        "${test_ansible_dir}/test/integration/Makefile"
fi

docker exec "${container_id}" mkdir -p "${test_shared_dir}/shippable/testresults"
docker exec "${container_id}" /bin/sh -c "cd '${test_ansible_dir}' && . hacking/env-setup && cd test/integration && \
    JUNIT_OUTPUT_DIR='${test_shared_dir}/shippable/testresults' ANSIBLE_CALLBACK_WHITELIST=junit \
    HTTPTESTER=1 TEST_FLAGS='${test_flags}' LC_ALL=en_US.utf-8 make ${test_target}"

tests_completed=1
