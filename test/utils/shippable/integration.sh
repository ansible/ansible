#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

test_image="${IMAGE}"
test_privileged="${PRIVILEGED:-false}"
test_flags="${TEST_FLAGS:-}"
test_target="${TARGET:-}"
test_ansible_dir="${TEST_ANSIBLE_DIR:-/root/ansible}"

http_image="${HTTP_IMAGE:-ansible/ansible:httptester}"

keep_containers="${KEEP_CONTAINERS:-}"
copy_source="${COPY_SOURCE:-}"

if [ "${SHIPPABLE_BUILD_DIR:-}" ]; then
    host_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
    controller_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
else
    host_shared_dir="${source_root}"
    controller_shared_dir=""
fi

if [ "${copy_source}" ]; then
    test_shared_dir="/shared"
else
    test_shared_dir="${test_ansible_dir}"
fi

container_id=
httptester_id=

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
show_environment

if [ "${controller_shared_dir}" ]; then
    cp -a "${SHIPPABLE_BUILD_DIR}" "${controller_shared_dir}"
fi

httptester_id=$(docker run -d "${http_image}")
container_id=$(docker run -d \
    -v "/sys/fs/cgroup:/sys/fs/cgroup:ro" \
    -v "${host_shared_dir}:${test_shared_dir}" \
    --link="${httptester_id}:ansible.http.tests" \
    --link="${httptester_id}:sni1.ansible.http.tests" \
    --link="${httptester_id}:sni2.ansible.http.tests" \
    --link="${httptester_id}:fail.ansible.http.tests" \
    --privileged="${test_privileged}" \
    "${test_image}")

show_environment

docker exec "${container_id}" pip install junit-xml

if [ "${copy_source}" ]; then
    docker exec "${container_id}" cp -a "${test_shared_dir}" "${test_ansible_dir}"
fi

docker exec "${container_id}" mkdir -p "${test_shared_dir}/shippable/testresults"
docker exec "${container_id}" /bin/sh -c "cd '${test_ansible_dir}' && . hacking/env-setup && cd test/integration && \
    JUNIT_OUTPUT_DIR='${test_shared_dir}/shippable/testresults' ANSIBLE_CALLBACK_WHITELIST=junit \
    HTTPTESTER=1 TEST_FLAGS='${test_flags}' LC_ALL=en_US.utf-8 make ${test_target}"
