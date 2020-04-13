#!/usr/bin/env bash

set -eux

OUTPUT_DIR=${OUTPUT_DIR:-$(mktemp -d)}

trap 'rm -rf "${OUTPUT_DIR}"' EXIT

# setup required roles
ln -s ../../prepare_tests roles/prepare_tests

# run old type role tests
ansible-playbook -i ../../inventory run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" -v "$@"

# run tests to avoid path injection from slurp when fetch uses become
ansible-playbook -i ../../inventory injection/avoid_slurp_return.yml -e "output_dir=${OUTPUT_DIR}" -v "$@"
