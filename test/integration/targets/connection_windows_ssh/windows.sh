#!/usr/bin/env bash

set -eux

cd ../connection

if [[ "$(scp -O 2>&1)" == "usage: scp "* ]]; then
    # scp supports the -O option (and thus the -T option as well)
    # work-around required
    # see: https://www.openssh.com/txt/release-9.0
    scp_args=("-e" "ansible_scp_extra_args=-TO")
elif [[ "$(scp -T 2>&1)" == "usage: scp "* ]]; then
    # scp supports the -T option
    # work-around required
    # see: https://github.com/ansible/ansible/issues/52640
    scp_args=("-e" "ansible_scp_extra_args=-T")
else
    # scp does not support the -T or -O options
    # no work-around required
    # however we need to put something in the array to keep older versions of bash happy
    scp_args=("-e" "")
fi

# A recent patch to OpenSSH causes a validation error when running through Ansible. It seems like if the path is quoted
# then it will fail with 'protocol error: filename does not match request'. We currently ignore this by setting
# 'ansible_scp_extra_args=-T' to ignore this check but this should be removed once that bug is fixed and our test
# container has been updated.
# https://unix.stackexchange.com/questions/499958/why-does-scps-strict-filename-checking-reject-quoted-last-component-but-not-oth
# https://github.com/openssh/openssh-portable/commit/391ffc4b9d31fa1f4ad566499fef9176ff8a07dc
INVENTORY="${OUTPUT_DIR}/test_connection.inventory" ./test.sh \
    -e target_hosts=windows \
    -e action_prefix=win_ \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=c:/windows/temp/ansible-remote \
    "${scp_args[@]}" \
    "$@"

cd ../connection_windows_ssh

ansible-playbook -i "${OUTPUT_DIR}/test_connection.inventory" tests_fetch.yml \
    "${scp_args[@]}" \
    "$@"
