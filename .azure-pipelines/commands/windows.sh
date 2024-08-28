#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"
connection="${args[2]}"
connection_setting="${args[3]}"
group="${args[4]}"

target="shippable/windows/group${group}/"

stage="${S:-prod}"
provider="${P:-default}"

# python versions to test in order
IFS=' ' read -r -a python_versions <<< \
    "$(PYTHONPATH="${PWD}/test/lib" python -c 'from ansible_test._internal import constants; print(" ".join(constants.CONTROLLER_PYTHON_VERSIONS))')"

# python version to run full tests on while other versions run minimal tests
python_default="$(PYTHONPATH="${PWD}/test/lib" python -c 'from ansible_test._internal import constants; print(constants.CONTROLLER_MIN_PYTHON_VERSION)')"

# version to test when only testing a single version
single_version=2022

# shellcheck disable=SC2086
ansible-test windows-integration --list-targets -v ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} > /tmp/explain.txt 2>&1 || { cat /tmp/explain.txt && false; }
{ grep ' windows-integration: .* (targeted)$' /tmp/explain.txt || true; } > /tmp/windows.txt

if [ -s /tmp/windows.txt ] || [ "${CHANGED:+$CHANGED}" == "" ]; then
    echo "Detected changes requiring integration tests specific to Windows:"
    cat /tmp/windows.txt

    echo "Running Windows integration tests for the version ${version}."
else
    echo "No changes requiring integration tests specific to Windows were detected."
    echo "Running Windows integration tests for a single version only: ${single_version}"

    if [ "${version}" != "${single_version}" ]; then
        echo "Skipping this job since it is for: ${version}"
        exit 0
    fi
fi

for py_version in "${python_versions[@]}"; do
    changed_all_target="all"
    changed_all_mode="default"

    if [ "${py_version}" == "${python_default}" ]; then
        # smoketest tests
        if [ "${CHANGED}" ]; then
            # with change detection enabled run tests for anything changed
            # use the smoketest tests for any change that triggers all tests
            ci="${target}"
            changed_all_target="shippable/windows/smoketest/"
            if [ "${target}" == "shippable/windows/group1/" ]; then
                # only run smoketest tests for group1
                changed_all_mode="include"
            else
                # smoketest tests already covered by group1
                changed_all_mode="exclude"
            fi
        else
            # without change detection enabled run entire test group
            ci="${target}"
        fi
    else
        # only run minimal tests for group1
        if [ "${target}" != "shippable/windows/group1/" ]; then continue; fi
        # minimal tests for other python versions
        ci="shippable/windows/minimal/"
    fi

    # terminate remote instances on the final python version tested
    if [ "${py_version}" = "${python_versions[-1]}" ]; then
        terminate="always"
    else
        terminate="never"
    fi

    # shellcheck disable=SC2086
    ansible-test windows-integration --color -v --retry-on-error "${ci}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
        --changed-all-target "${changed_all_target}" --changed-all-mode "${changed_all_mode}" \
        --controller "docker:default,python=${py_version}" \
        --target "remote:windows/${version},connection=${connection}+${connection_setting},provider=${provider}" \
        --remote-terminate "${terminate}" --remote-stage "${stage}"
done
