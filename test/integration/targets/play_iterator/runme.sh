#!/usr/bin/env bash

set -eux

ansible-playbook playbook.yml --start-at-task 'task 2' "$@"
