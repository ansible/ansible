#!/usr/bin/env bash

set -eux

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

# sftp
./posix.sh "$@"
# scp
ANSIBLE_SSH_TRANSFER_METHOD=scp ./posix.sh "$@" "${scp_args[@]}"
# piped
ANSIBLE_SSH_TRANSFER_METHOD=piped ./posix.sh "$@"

# test config defaults override
ansible-playbook check_ssh_defaults.yml "$@" -i test_connection.inventory

# ensure we can load from ini cfg
ANSIBLE_CONFIG=./test_ssh_defaults.cfg ansible-playbook verify_config.yml "$@"

# ensure we handle cp with spaces correctly, otherwise would fail with
# `"Failed to connect to the host via ssh: command-line line 0: keyword controlpath extra arguments at end of line"`
ANSIBLE_SSH_CONTROL_PATH='/tmp/ssh cp with spaces' ansible -m ping all -e ansible_connection=ssh -i test_connection.inventory "$@"
