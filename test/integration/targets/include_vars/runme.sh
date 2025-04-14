#!/usr/bin/env bash

set -eux

TEST_DIR="$(pwd)"

# run from a different dir so CWD != playbook dir, to verify include_vars dirs are resolved relative to the playbook dir
(cd / && ansible-playbook -i "${TEST_DIR}/../../inventory" "${TEST_DIR}/test_as_playbook.yml")

export ANSIBLE_ROLES_PATH=../

ansible-playbook -i ../../inventory test_as_role.yml
