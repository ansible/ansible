#!/usr/bin/env bash

set -eux

ANSIBLE_COLLECTIONS_PATH="${PWD}/collection_root" ansible-playbook test.yml -i ../../inventory "$@"
