#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook import.yml -i ../../inventory "${@}"
