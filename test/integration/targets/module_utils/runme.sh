#!/usr/bin/env bash

set -eux

ansible-playbook module_utils_test.yml -i ../../inventory -v "$@"
