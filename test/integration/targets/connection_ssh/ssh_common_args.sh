#!/usr/bin/env bash

set -eux

rm -f test-ansible.cfg  # just in case

trap 'cleanup' EXIT

remote_user=tmp_ansible_test_user
remote_user_var="-e remote_unprivileged_user=${remote_user}"

# Set ANSIBLE_SSH_ARGS to empty string in order to disable ControlPersist (otherwise second playbook will use same remote user than first playbook)
export ANSIBLE_SSH_ARGS=""

# Create remote user and test-ansible.cfg
ansible-playbook -i test_connection.inventory -v "${remote_user_var}" setup_ssh_common_args.yml "$@"

# Ensure --ssh-common-args is taken in account (test-ansible.cfg not used)
ansible-playbook -i test_connection.inventory -v "${remote_user_var}" test_ssh_common_args.yml --ssh-common-args="-o \"User=${remote_user}\"" "$@"

# Check that ssh_common_args in test-ansible.cfg is taken in account
ANSIBLE_CONFIG=./test-ansible.cfg ansible-playbook -i test_connection.inventory -v "${remote_user_var}" test_ssh_common_args.yml "$@"

function cleanup {
    ansible-playbook -i test_connection.inventory -v "${remote_user_var}" clean_ssh_common_args.yml "$@"
}
