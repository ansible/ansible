#!/usr/bin/env bash

set -eux

ansible-playbook -i inventory playbook.yml -v "$@"
