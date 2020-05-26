#!/usr/bin/env bash

set -eux

export ANSIBLE_COLLECTIONS_PATHS=$PWD/test_collections

ansible-playbook test_redirected_module_defaults.yml -vvv
