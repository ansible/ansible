#!/usr/bin/env bash

set -eux
trap 'ansible-playbook -i ../../inventory cleanup.yml -b "$@"' EXIT

# setup required roles
ln -s ../../setup_remote_tmp_dir roles/setup_remote_tmp_dir

# run old type role tests
ansible-playbook -i ../../inventory run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# run same test with become
ansible-playbook -i ../../inventory run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" -b "$@"

# run tests to avoid path injection from slurp when fetch uses become
ansible-playbook -i ../../inventory injection/avoid_slurp_return.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# Test unreadable file with stat. Requires running without become and as a user other than root.
export ANSIBLE_SSH_EXTRA_ARGS="-o UserKnownHostsFile=/dev/null"
ansible-playbook -i hosts.yml setup_unreadable_test.yml -e "output_dir=${OUTPUT_DIR}" "$@"
ansible-playbook --user fetcher -i hosts.yml test_unreadable_with_stat.yml -e "output_dir=${OUTPUT_DIR}" "$@"
unset ANSIBLE_SSH_EXTRA_ARGS
