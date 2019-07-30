#!/usr/bin/env bash

set -eux

ansible-playbook test_include_file_noop.yml -i inventory "$@"
