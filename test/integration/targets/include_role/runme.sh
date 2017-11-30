#!/usr/bin/env bash

set -eux

ansible-playbook test_include_role.yml -i ../../inventory "$@"
