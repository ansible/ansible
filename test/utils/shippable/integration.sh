#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

test_image="${IMAGE:-ansible/ansible:centos7}"
test_flags="${TEST_FLAGS:-}"
test_target="${TARGET:-all}"
test_ansible_dir="${TEST_ANSIBLE_DIR:-/root/ansible}"
test_python3="${PYTHON3:-}"
test_tags="${TEST_TAGS:-}"
skip_tags="${SKIP_TAGS:-}"

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

# The build directory used by Shippable.
# It is assumed tests are running on Shippable when this value is set.
shippable_build_dir="${SHIPPABLE_BUILD_DIR:-}"

if [ "${shippable_build_dir}" ]; then
    host_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
    controller_shared_dir="/home/shippable/cache/build-${BUILD_NUMBER}"
    share_source=1
else
    host_shared_dir="${source_root}"
    controller_shared_dir=""
fi

if [ -z "${share_source}" ]; then
    test_shared_dir="/shared"
else
    test_shared_dir="${test_ansible_dir}"
fi

container_ids=()
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
    set -x

    if [ "${controller_shared_dir}" ]; then
        cp -av "${controller_shared_dir}/shippable" "${shippable_build_dir}"
        rm -rf "${controller_shared_dir}"
    fi

    if [ "${keep_containers}" == "onfailure" ] && [ "${tests_completed}" != "" ]; then
        keep_containers=
    fi

    if [ "${keep_containers}" == "" ] && [ ${#container_ids[*]} ]; then
        docker rm -f "${container_ids[@]}" || true
    fi

    show_environment
}

function run_container
{
    local target
    local tags
    local privileged

    target="$1"
    tags="$2"
    privileged="$3"

    local container_id
    container_id=$(docker run -d \
        --env "ANSIBLE_FORCE_COLOR=${force_color}" \
        -v "/sys/fs/cgroup:/sys/fs/cgroup:ro" \
        -v "${host_shared_dir}:${test_shared_dir}" \
        --link="${httptester_id}:ansible.http.tests" \
        --link="${httptester_id}:sni1.ansible.http.tests" \
        --link="${httptester_id}:sni2.ansible.http.tests" \
        --link="${httptester_id}:fail.ansible.http.tests" \
        --privileged="${privileged}" \
        "${test_image}")

    container_ids+=(${container_id})

    show_environment

    local skip
    skip="${skip_tags}"

    if [ "${test_python3}" ]; then
        docker exec "${container_id}" ln -s /usr/bin/python3 /usr/bin/python
        docker exec "${container_id}" ln -s /usr/bin/pip3 /usr/bin/pip

        skip+=",$(tr '\n' ',' < "${source_root}/test/utils/shippable/python3-test-tag-blacklist.txt")"
    fi

    if [ "${privileged}" == "false" ]; then
        skip+=",needs_privileged"
    fi

    local flags
    flags=""

    if [ "${tags}" ]; then
        flags+=" --tags ${tags}"
    fi

    if [ "${skip}" ]; then
        flags+=" --skip-tags ${skip}"
    fi

    if [ "${test_flags}" ]; then
        flags+=" ${test_flags}"
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
        HTTPTESTER=1 TEST_FLAGS='${flags}' LC_ALL=en_US.utf-8 make ${target}"
}

function run_privileged_container
{
    local requested_targets
    requested_targets=($1)

    local requested_tags
    requested_tags=($(echo "$2" | tr ',' '\n'))

    local supported_targets
    supported_targets=(destructive non_destructive)

    local candidate
    local requested

    ### Expand Targets

    local selected_targets
    selected_targets=()

    # Generate a list of targets using the supported target list and the requested target list.
    for candidate in "${supported_targets[@]}"; do
        for requested in "${requested_targets[@]}"; do
            if [ "${requested}" == "${candidate}" ] || [ "${requested}" == "all" ]; then
                selected_targets+=("${candidate}")
                break
            fi
        done
    done

    set +x

    echo
    echo "[Targets]"
    echo "Supported: ${supported_targets[*]}"
    echo "Requested: ${requested_targets[*]}"
    echo " Selected: ${selected_targets[*]:-}"
    echo

    if [ ${#selected_targets[@]} -eq 0 ]; then
        echo "No supported targets specified, skipping privileged tests."
        echo

        set -x
        return
    fi

    set -x

    ### Expand Tags

    local supported_tags
    supported_tags=()

    # Identify unique tags from the selected targets which require a privileged container.
    for requested in "${selected_targets[@]}"; do
        supported_tags+=($(grep 'needs_privileged' "${source_root}/test/integration/${requested}.yml" | \
            sed 's/^.*tags: *\[//; s/\].*$//; s/,/ /g;'))
    done

    # Make sure the list of tags is sorted and unique.
    supported_tags=($(echo "${supported_tags[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

    local selected_tags

    # Determine which tags should be used.
    if [ ${#requested_tags[@]} -eq 0 ]; then
        selected_tags=(${supported_tags[@]})
    else
        selected_tags=()

        # Generate a list of tags using the supported tags list and the requested tags list.
        for candidate in "${supported_tags[@]}"; do
            for requested in "${requested_tags[@]}"; do
                if [ "${requested}" == "${candidate}" ] || [ "${requested}" == "all" ]; then
                    selected_tags+=("${candidate}")
                    break
                fi
            done
        done

        selected_tags=($(echo "${selected_tags[@]:-}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
    fi

    set +x

    echo
    echo "[Tags]"
    echo "Supported: ${supported_tags[*]}"
    echo "Requested: ${requested_tags[*]:-}"
    echo " Selected: ${selected_tags[*]:-}"
    echo

    if [ ${#selected_tags[@]} -eq 0 ]; then
        echo "No supported tags specified, skipping privileged tests."
        echo

        set -x
        return
    fi

    set -x

    # Convert the selected tags back to a comma separated list.
    local tag_string
    tag_string=$(echo "${selected_tags[*]}" | tr ' ' ',')

    # Run tests using the selected target(s) and tag(s) in privileged mode.
    run_container "${selected_targets[*]}" "${tag_string}" "true"
}

trap cleanup EXIT INT TERM
docker images ansible/ansible

show_environment

if [ "${controller_shared_dir}" ]; then
    cp -a "${shippable_build_dir}" "${controller_shared_dir}"
fi

httptester_id=$(docker run -d "${http_image}")
container_ids+=(${httptester_id})

# Tests which are tagged with 'needs_privileged' require docker containers running in privileged mode.
# This requirement varies depending on the test involved and the distribution and version of the container.
# Unfortunately, running all containers in privileged mode results in a severe performance hit, which causes timeouts.
# Some distributions will always see this performance hit, while it is random for others.
# Using alternative methods to run the tests, such as using --cap-add SYS_ADMIN, results in the same problem.
# Additionally, using capabilities instead of privileged mode runs into issues with AppArmor restrictions.
# To deal with this we run most tests unprivileged, and separately run privileged tests as needed.
# Privileged mode is used for any test which requires it, even if not all distributions or versions require it.
# This is done to reduce complexity, as we don't have to care which image is being used for needs_privileged tests.

run_container            "${test_target}" "${test_tags}" "false"
run_privileged_container "${test_target}" "${test_tags}"

tests_completed=1
