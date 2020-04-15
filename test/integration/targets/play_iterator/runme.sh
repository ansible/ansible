#!/usr/bin/env bash

set -ux

ansible-playbook playbook.yml -vvv --start-at-task 'task 2' "$@"
