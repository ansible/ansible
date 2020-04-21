#!/usr/bin/env bash

set -eux

# check check
ansible-playbook check_magic_var.yml --check -e '{"expect": true}' --tags 'check'
ansible-playbook check_magic_var.yml -e '{"expect": false}' --tags 'check'

# diff check
ansible-playbook check_magic_var.yml --diff -e '{"expect": true}' --tags 'diff'
ansible-playbook check_magic_var.yml '{"expect": false}' --tags 'diff'
