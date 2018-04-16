#!/usr/bin/env bash

set -eux

ANSIBLE_EXPAND_PATH_FILE_TESTS=1 ansible-playbook file.yml -v "$@"
