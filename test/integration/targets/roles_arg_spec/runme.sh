#!/usr/bin/env bash

set -eux

# Various simple role scenarios
ansible-playbook test.yml -i ../../inventory "$@"

# More complex role test
ansible-playbook test_complex_role_fails.yml -i ../../inventory "$@"

# Test play level role will fail
set +e
ansible-playbook test_play_level_role_fails.yml -i ../../inventory "$@"
test $? -ne 0
set -e
