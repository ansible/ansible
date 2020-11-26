#!/usr/bin/env bash

set -eux

ansible-playbook test_defaults.yml "$@"
