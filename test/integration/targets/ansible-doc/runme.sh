#!/usr/bin/env bash

set -eux
ansible-playbook test.yml -i inventory "$@"
