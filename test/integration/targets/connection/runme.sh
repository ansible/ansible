#!/usr/bin/env bash

set -o nounset -o errexit -o xtrace

ANSIBLE_CONNECTION_PLUGINS="$(pwd)/plugin" ansible-playbook -i inventory "$(pwd)/play.yml" -v "$@"
