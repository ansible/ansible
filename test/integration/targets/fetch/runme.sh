#!/usr/bin/env bash

set -eux

function cleanup {
    ansible-playbook -i "${INVENTORY_PATH}" cleanup.yml -e "output_dir=${OUTPUT_DIR}" -b "$@"
    unset ANSIBLE_CACHE_PLUGIN
    unset ANSIBLE_CACHE_PLUGIN_CONNECTION
}

trap 'cleanup "$@"' EXIT

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
ansible-playbook -i "${INVENTORY_PATH}" setup_unreadable_test.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# Run the tests as the unprivileged user without become to test the use of the stat module from the fetch module
ansible-playbook -i "${INVENTORY_PATH}" test_unreadable_with_stat.yml -e ansible_user=fetcher -e ansible_become=no -e "output_dir=${OUTPUT_DIR}" "$@"
