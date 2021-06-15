#!/usr/bin/env bash

set -eux

function cleanup {
    ansible-playbook -i hosts.yml cleanup.yml -b "$@"
    unset ANSIBLE_SSH_EXTRA_ARGS
    unset ANSIBLE_CACHE_PLUGIN
    unset ANSIBLE_CACHE_PLUGIN_CONNECTION
}

trap 'cleanup "$@"' EXIT

export ANSIBLE_SSH_COMMON_ARGS="-o UserKnownHostsFile=/dev/null"

# setup required roles
ln -s ../../setup_remote_tmp_dir roles/setup_remote_tmp_dir

# run old type role tests
ansible-playbook -i ../../inventory run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# run same test with become
ansible-playbook -i ../../inventory run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" -b "$@"

# run tests to avoid path injection from slurp when fetch uses become
ansible-playbook -i ../../inventory injection/avoid_slurp_return.yml -e "output_dir=${OUTPUT_DIR}" "$@"

## Test unreadable file with stat. Requires running without become and as a user other than root.
#
# Change the known_hosts file to avoid changing the test environment
export ANSIBLE_CACHE_PLUGIN=jsonfile
export ANSIBLE_CACHE_PLUGIN_CONNECTION="${OUTPUT_DIR}/cache"
# Create a non-root user account and configure SSH acccess for that account
ansible-playbook -i hosts.yml setup_unreadable_test.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# Run the tests as the unprivileged user without become to test the use of the stat module from the fetch module
ansible-playbook --user fetcher -i hosts.yml test_unreadable_with_stat.yml -e "output_dir=${OUTPUT_DIR}" "$@"
