#!/usr/bin/env bash

set -eux
ansible-playbook test.yml -i ../../inventory "$@"
ansible-playbook test_include_role_fails.yml -i ../../inventory "$@"
