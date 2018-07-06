#!/usr/bin/env bash

set -ux

ansible-playbook -i ../../inventory playbook.yml -v "$@"
