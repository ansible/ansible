#!/usr/bin/env bash

set -o nounset -o errexit -o xtrace

ansible-playbook -i inventory "play.yml" -v "$@"
