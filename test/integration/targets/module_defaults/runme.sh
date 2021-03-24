#!/usr/bin/env bash

set -eux

ansible-playbook test_defaults.yml "$@"

ansible-playbook test_action_groups.yml "$@"
