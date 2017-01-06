#!/usr/bin/env bash

set -eux

ansible-playbook test_environment.yml -i ../../inventory "$@"
