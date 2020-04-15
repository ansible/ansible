#!/usr/bin/env bash

set -ux

ansible-playbook playbook.yml --start-at-task 'task 2' "$@"
