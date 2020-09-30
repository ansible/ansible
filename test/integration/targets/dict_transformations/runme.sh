#!/usr/bin/env bash

set -eux

ansible-playbook test_convert_snake_case.yml "$@"

ansible-playbook test_convert_camelCase.yml "$@"
