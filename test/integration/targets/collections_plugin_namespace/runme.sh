#!/usr/bin/env bash

set -eux

ANSIBLE_COLLECTIONS_PATHS="${PWD}/collection_root" ansible-playbook test.yml -i ../../inventory "$@"
