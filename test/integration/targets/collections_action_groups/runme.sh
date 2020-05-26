#!/usr/bin/env bash

set -eux

export ANSIBLE_COLLECTIONS_PATHS=$PWD/test_collections

ansible-playbook test_action_defaults.yml -vvv
